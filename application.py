import flask_migrate
# import json
import os
import tarfile
import uuid

from celery import Celery
from flask import Flask, Response, abort, jsonify, make_response, redirect, render_template, request, url_for, has_app_context
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from raven.contrib.flask import Sentry
from sqlalchemy.sql import func
from tempfile import gettempdir, mkstemp
from celery.result import AsyncResult

from compare import compare as compare50
from util import save, walk, walk_submissions

db_uri = "mysql://{}:{}@{}/{}".format(
    os.environ["MYSQL_USERNAME"],
    os.environ["MYSQL_PASSWORD"],
    os.environ["MYSQL_HOST"],
    os.environ["MYSQL_DATABASE"])

# Application
app = Flask(__name__)

# Monitoring
Sentry(app)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app, db)

# Enable UUID-based routes
FlaskUUID(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Run celery tasks in Flask context
# https://stackoverflow.com/questions/12044776/how-to-use-flask-sqlalchemy-in-a-celery-task
class FlaskCelery(Celery):
    def __init__(self, *args, **kwargs):

        super(FlaskCelery, self).__init__(*args, **kwargs)
        self.patch_task()

        if 'app' in kwargs:
            self.init_app(kwargs['app'])

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                if has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
                else:
                    with _celery.app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app
        self.config_from_object(app.config)


celery = FlaskCelery("compare50",
                     backend="db+mysql://{}:{}@{}/celerydb".format(
                         os.environ["MYSQL_USERNAME"],
                         os.environ["MYSQL_PASSWORD"],
                         os.environ["MYSQL_HOST"]),
                     broker="amqp://localhost",
                     app=app)


class Upload(db.Model):
    """Represents a particular batch of uploaded submissions"""
    id = db.Column(db.INT, primary_key=True)
    uuid = db.Column(db.CHAR(36), nullable=False, unique=True)
    created = db.Column(db.TIMESTAMP, nullable=False, default=func.now())
    passes = db.relationship("Pass", backref="upload")
    submissions = db.relationship("Submission", backref="upload")


class Pass(db.Model):
    """Represents a run of a preprocessing and fingerprinting
    configuration for on an upload"""
    id = db.Column(db.INT, primary_key=True)
    # TODO: make config rich enough to re-run pass
    config = db.Column(db.VARCHAR(255), nullable=False)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    hashes = db.relationship("Hash", backref="processor")
    matches = db.relationship("Match", backref="processor")

    def __init__(self, config):
        self.config = config


class Submission(db.Model):
    """Represents a student's submission comprised of some number of files"""
    id = db.Column(db.INT, primary_key=True)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    path = db.Column(db.VARCHAR(255), nullable=False)
    files = db.relationship("File", backref="submission")


class File(db.Model):
    """Represents a single uploaded file"""
    id = db.Column(db.INT, primary_key=True)
    submission_id = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    path = db.Column(db.VARCHAR(255), nullable=False)
    fragments = db.relationship("Fragment", backref="file")


class Hash(db.Model):
    """Represents a chunk of code that may be contained within multiple files"""
    id = db.Column(db.INT, primary_key=True)
    pass_id = db.Column(db.INT, db.ForeignKey("pass.id", ondelete="CASCADE"), nullable=False)
    fragments = db.relationship("Fragment", backref="hash")


class Fragment(db.Model):
    """Represents a particular section of text in a file"""
    id = db.Column(db.INT, primary_key=True)
    hash_id = db.Column(db.INT, db.ForeignKey("hash.id", ondelete="CASCADE"), nullable=False)
    file_id = db.Column(db.INT, db.ForeignKey("file.id", ondelete="CASCADE"), nullable=False)
    start = db.Column(db.INT, nullable=False)
    end = db.Column(db.INT, nullable=False)


class Match(db.Model):
    """Represents a pair of submissions scored by a pass"""
    id = db.Column(db.INT, primary_key=True)
    sub_a = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    sub_b = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    pass_id = db.Column(db.INT, db.ForeignKey("pass.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.INT, nullable=False)


@app.before_first_request
def before_first_request():

    # Perform any migrates
    flask_migrate.upgrade()

    # Create database for celery
    db.engine.execute("CREATE DATABASE IF NOT EXISTS celerydb;")


@app.route("/", methods=["GET"])
def get():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def post():

    # Check for files
    if not request.files.getlist("submissions"):
        abort(make_response(jsonify(error="missing submissions"), 400))

    # Unique parent
    id = str(uuid.uuid4())
    parent = os.path.join(gettempdir(), id)
    try:
        os.mkdir(parent)
    except FileExistsError:
        abort(500)

    # Save submissions
    submissions = os.path.join(parent, "submissions")
    os.mkdir(submissions)
    for file in request.files.getlist("submissions"):
        print(file)
        print(file.headers)
        print(file.filename)
        save(file, submissions)

    # Save distros, if any
    if request.files.getlist("distros"):
        distros = os.path.join(parent, "distros")
        os.mkdir(distros)
        for file in request.files.getlist("distros"):
            save(file, distros)
    else:
        distros = None

    # Save archives, if any
    if request.files.getlist("archives"):
        archives = os.path.join(parent, "archives")
        os.mkdir(archives)
        for file in request.files.getlist("archives"):
            save(file, archives)
    else:
        archives = None

    compare_task.apply_async(task_id=id)

    # Redirect to results
    return redirect(url_for("results", id=id))


@app.route("/<uuid:id>")
def results(id):
    result = AsyncResult(id)
    print(f"Task status: {result.state}")
    if result.state == "FAILURE":
        print(result.result)
        # TODO: return error page to user
    elif result.state == "SUCCESS":
        upload = Upload.query.filter_by(uuid=id).first_or_404()
        passes = []
        paths = {}
        matches = {}
        for p in upload.passes:
            passes.append(p.config)
            for match in p.matches:
                paths[match.sub_a] = Submission.query.get(match.sub_a).path
                paths[match.sub_b] = Submission.query.get(match.sub_b).path
                matches.setdefault((match.sub_a, match.sub_b), {})[p.config] = match.score
        return render_template("results.html", id=id, passes=passes, paths=paths, matches=matches)
    # TODO: return loading message
    return jsonify(walk(os.path.join(gettempdir(), str(id))))


@app.route("/<uuid:id>/compare")
def compare(id):
    # check the worker has finished
    result = AsyncResult(id)
    if result.state != "SUCCESS":
        return redirect(f"/{id}")

    # validate args
    a = request.args.get("a")
    b = request.args.get("b")
    if a is None or b is None or not a.isdigit() or not b.isdigit():
        # TODO: error instead?
        return redirect(f"/{id}")

    # check that comparison exists and has correct upload id
    match = Match.query.filter_by(sub_a=a, sub_b=b).first()
    if match is None or match.processor.upload.uuid != str(id):
        return redirect(f"/{id}")


    sub_a = Submission.query.get(match.sub_a)
    sub_b = Submission.query.get(match.sub_b)
    a_frags = Fragment.query.join(File.fragments).\
              filter(File.submission_id == sub_a.id)
    b_frags = Fragment.query.join(File.fragments).\
              filter(File.submission_id == sub_b.id)

    # reduce to only shared fragments
    a_shared = a_frags.filter(Fragment.hash_id.\
                             in_(b_frags.with_entities(Fragment.hash_id))).all()
    b_shared = b_frags.filter(Fragment.hash_id.\
                             in_(a_frags.with_entities(Fragment.hash_id))).all()

    a_by_hash = {}
    b_by_hash = {}
    for dest, src in ((a_by_hash, a_shared), (b_by_hash, b_shared)):
        for frag in src:
            dest.setdefault(frag.hash_id, []).append(frag)

    def expand_frags(a_frags, b_frags):
        data = tuple([(frag, frag.start, frag.end) for frag in frags]
                     for frags in (a_frags, b_frags))

        while True:
            changed = False
            prevs = set()
            nexts = set()
            for sub_data in data:
                for frag, start, end in sub_data:
                    path = os.path.join(gettempdir(),
                                        frag.file.submission.upload.uuid,
                                        frag.file.submission.path,
                                        frag.file.path)
                    with open(path, "r") as f:
                        text = f.read()
                        prevs.add(text[start-1] if start > 0 else None)
                        nexts.add(text[end] if end < len(text) else None)
            if len(prevs) == 1 and prevs.pop() is not None:
                data = tuple([(frag, start-1, end) for frag, start, end in data]
                             for data in data)
                changed = True
            if len(nexts) == 1 and nexts.pop() is not None:
                data = tuple([(frag, start, end+1) for frag, start, end in data]
                             for data in data)
                changed = True
            if not changed:
                break
        return data

    a_expanded = []
    b_expanded = []
    for h in set(a_by_hash) | set(b_by_hash):
        a, b = expand_frags(a_by_hash[h], b_by_hash[h])
        a_expanded.extend(a)
        b_expanded.extend(b)

    a_by_file = {f: [] for f in sub_a.files}
    b_by_file = {f: [] for f in sub_b.files}
    for dest, src in ((a_by_file, a_expanded), (b_by_file, b_expanded)):
        for frag, start, end in src:
            dest[frag.file].append((frag, start, end))

    def flatten_frags(file, frags):
        """Return list of (text, hash ids) pairs"""
        def get_hash(f):
            return f[0].hash_id

        def get_start(f):
            return f[1]

        def get_end(f):
            return f[2]

        path = os.path.join(gettempdir(),
                            file.submission.upload.uuid,
                            file.submission.path,
                            file.path)
        with open(path, "r") as file:
            text = file.read()
        frags = sorted(frags, key=get_start)
        result = []
        cur_frags = []
        cur_text = []

        def make_output():
            return ("".join(cur_text),
                    " ".join(str(get_hash(f)) for f in cur_frags))

        for i, c in enumerate(text):
            new_frags = [f for f in cur_frags if get_end(f) > i]
            while frags and get_start(frags[0]) == i:
                new_frags.append(frags.pop(0))
            if new_frags != cur_frags and cur_text:
                result.append(make_output())
                cur_text = []
            cur_frags = new_frags
            cur_text.append(c)
        result.append(make_output())
        return result

    a_files = [(f.path, flatten_frags(f, a_by_file[f])) for f in sub_a.files]
    b_files = [(f.path, flatten_frags(f, b_by_file[f])) for f in sub_b.files]
    return render_template("compare.html", a_files=a_files, b_files=b_files)


@celery.task(bind=True)
def compare_task(self):
    parent = os.path.join(gettempdir(), self.request.id)

    # find directories where files were saved
    submission_dir = os.path.join(parent, "submissions")
    distro_dir = os.path.join(parent, "distros")
    archive_dir = os.path.join(parent, "archives")

    # get submission lists
    submissions = walk_submissions(submission_dir)
    distros = walk(distro_dir) if os.path.exists(distro_dir) else []
    archives = walk_submissions(archive_dir) if os.path.exists(archive_dir) else []

    print("Running comparison")
    passes, files, subs, spans, results = compare50.compare(submissions, distros, archives)

    print("Storing data")

    # create upload
    upload = Upload()
    upload.uuid = self.request.id

    # create passes
    db_passes = {pass_name: Pass(pass_name) for pass_name in passes}
    upload.passes = list(db_passes.values())

    # create submissions and files
    db_submissions = [None] * len(subs)
    db_files = {}
    for i, sub in enumerate(subs):
        if len(sub) == 0:
            continue

        s = db_submissions[i] = Submission()
        upload.submissions.append(s)

        # path of submission
        if len(sub) == 1:
            sub_root = os.path.dirname(files[sub[0]])
        else:
            sub_root = os.path.commonpath([files[f] for f in sub])
        s.path = os.path.relpath(sub_root, parent)

        # add files to submission
        for i in sub:
            f = db_files[i] = File()
            s.files.append(f)
            f.path = os.path.relpath(files[i], sub_root)

    for pass_name, spans in spans.items():
        # map hashes to spans
        hashes = {}
        for span in spans:
            hashes.setdefault(span.hash, set()).add(span)

        # create hashes and fragments
        for hash, spans in hashes.items():
            h = Hash()
            db_passes[pass_name].hashes.append(h)
            for span in spans:
                s = Fragment()
                s.start = span.start
                s.end = span.stop
                db_files[span.file].fragments.append(s)
                h.fragments.append(s)

    # commit so we can access submission IDs below
    db.session.add(upload)
    db.session.commit()

    # create scored matches
    for pass_name, scores in results.items():
        for (sub_a, sub_b), score in scores.items():
            m = Match()
            m.sub_a = db_submissions[sub_a].id
            m.sub_b = db_submissions[sub_b].id
            m.score = score
            db_passes[pass_name].matches.append(m)

    db.session.add(upload)
    db.session.commit()
