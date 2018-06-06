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
from util import save, walk, walk_submissions, submission_path, NotFinishedException, InvalidRequestException

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
    matches = db.relationship("Match", backref="processor")


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


class Match(db.Model):
    """Represents a pair of submissions scored by a pass"""
    id = db.Column(db.INT, primary_key=True)
    sub_a = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    sub_b = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    pass_id = db.Column(db.INT, db.ForeignKey("pass.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.INT, nullable=False)


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
    submission_dir = os.path.join(parent, "submissions")
    os.mkdir(submission_dir)
    for file in request.files.getlist("submissions"):
        print(file)
        print(file.headers)
        print(file.filename)
        save(file, submission_dir)

    # Save distros, if any
    if request.files.getlist("distros"):
        distros_dir = os.path.join(parent, "distros")
        os.mkdir(distros_dir)
        for file in request.files.getlist("distros"):
            save(file, distros_dir)
    else:
        distros_dir = None

    # Save archives, if any
    if request.files.getlist("archives"):
        archives_dir = os.path.join(parent, "archives")
        os.mkdir(archives_dir)
        for file in request.files.getlist("archives"):
            save(file, archives_dir)
    else:
        archives_dir = None

    # create upload, submissions, and files in database
    upload = Upload()
    upload.uuid = id

    submissions = walk_submissions(submission_dir)
    distros = walk(distros_dir) if distros_dir else []
    archives = walk_submissions(archives_dir) if archives_dir else []

    for sub in [distros] + submissions + archives:
        if len(sub) == 0:
            continue
        s = Submission()
        sub_path = submission_path(sub)
        s.path = os.path.relpath(sub_path, parent)
        upload.submissions.append(s)

        # add files
        for file in sub:
            f = File()
            s.files.append(f)
            f.path = os.path.relpath(file, sub_path)

    db.session.add(upload)
    db.session.commit()

    # TODO: remove and replace with dynamic pass runner
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
def compare_view(id):
    try:
        a, b = request.args.get("a"), request.args.get("b")
        a_files, b_files = compare(id, a, b)
    except (NotFinishedException, InvalidRequestException) as e:
        print(e)
        return redirect(f"/{id}")

    return render_template("compare.html", a_files=a_files, b_files=b_files)


@app.route("/api/<uuid:id>/compare")
def compare_api(id):
    try:
        a, b = request.args.get("a"), request.args.get("b")
        result = compare(id, a, b)
    except (NotFinishedException, InvalidRequestException):
        abort(status.HTTP_400_BAD_REQUEST)

    # TODO: add keys to JSON instead of just having a ton of nested lists
    return jsonify(result)


def compare(id, a, b):
    """Takes a job ID and two unvalidated submission IDs and returns two
    lists of (path, flattened fragments) pairs, where each flattened fragment
    is a (text, fragment IDs) pair
    """
    # check the worker has finished
    result = AsyncResult(id)
    if result.state != "SUCCESS":
        # TODO: differentiate between pending and failure
        raise NotFinishedException()

    # validate args
    a = request.args.get("a")
    b = request.args.get("b")
    if a is None or b is None or not a.isdigit() or not b.isdigit():
        raise InvalidRequestException()

    # check that comparison exists and has correct upload id
    match = Match.query.filter_by(sub_a=a, sub_b=b).first()
    if match is None or match.processor.upload.uuid != str(id):
        raise InvalidRequestException()

    # TODO: proper pairwise comparison here
    a_texts, b_texts = [], []
    for dest, src in ((a_texts, a), (b_texts, b)):
        sub = Submission.query.get(src)
        for file in sub.files:
            with open(os.path.join(gettempdir(),
                                   str(id),
                                   sub.path,
                                   file.path)) as f:
                dest.append((file.path, [(f.read(), [])]))
    return a_texts, b_texts


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

    upload = Upload.query.filter_by(uuid=self.request.id).first()

    for pass_name, (preprocessor, comparator) in compare50.DEFAULT_CONFIG.items():
        scores = compare50.compare(preprocessor, comparator,
                                          submissions, distros, archives)
        # create pass
        p = Pass()
        p.config = pass_name
        upload.passes.append(p)

        for (sub_a, sub_b), score in scores.items():
            path_a = os.path.relpath(submission_path(sub_a), parent)
            path_b = os.path.relpath(submission_path(sub_b), parent)
            sub_a = Submission.query.filter_by(path=path_a, upload_id=upload.id).first()
            sub_b = Submission.query.filter_by(path=path_b, upload_id=upload.id).first()
            m = Match()
            m.sub_a = sub_a.id
            m.sub_b = sub_b.id
            m.score = score
            p.matches.append(m)

    db.session.commit()
