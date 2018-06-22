import bisect
import flask_migrate
import os
import tarfile
import uuid

from flask import (
    Flask,
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from raven.contrib.flask import Sentry
from sqlalchemy.sql import func
from tempfile import gettempdir, mkstemp
from celery.result import AsyncResult

import pygments
import pygments.lexers
import pygments.lexers.special

from config import DEFAULT_CONFIG
from data import Fragment, MatchResult, Token, Span
from util import FlaskCelery, save, walk, walk_submissions, submission_path


# Application
app = Flask(__name__)


# Monitoring
Sentry(app)


# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://{}:{}@{}/{}".format(
    os.environ["MYSQL_USERNAME"],
    os.environ["MYSQL_PASSWORD"],
    os.environ["MYSQL_HOST"],
    os.environ["MYSQL_DATABASE"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app, db)


# Enable UUID-based routes
FlaskUUID(app)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
    all_submissions = db.relationship("Submission", backref="upload")

    # TODO: can these associations be expressed as relationships in SQLAlchemy?
    @property
    def submissions(self):
        res = Submission.query.filter_by(upload_id=self.id).join(Submissions).all()
        return res if res is not None else []

    @property
    def archives(self):
        res = Submission.query.filter_by(upload_id=self.id).join(Archives).all()
        return res if res is not None else []

    @property
    def distro(self):
        res = Submission.query.filter_by(upload_id=self.id).join(Distros).first()
        return res if res is not None else []

    @property
    def full_path(self):
        return os.path.join(gettempdir(), str(self.uuid))

    @property
    def submission_dir(self):
        return os.path.join(self.full_path, "submissions")

    @property
    def archive_dir(self):
        return os.path.join(self.full_path, "archives")

    @property
    def distro_dir(self):
        return os.path.join(self.full_path, "distros")


class Submission(db.Model):
    """Represents a student's submission comprised of some number of files"""
    id = db.Column(db.INT, primary_key=True)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    path = db.Column(db.VARCHAR(255), nullable=False)
    files = db.relationship("File", backref="submission")

    @property
    def full_path(self):
        return os.path.join(self.upload.full_path, self.path)


class Submissions(db.Model):
    """Maps uploads to their submissions"""
    id = db.Column(db.INT, primary_key=True)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    submission_id = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)


class Archives(db.Model):
    """Maps uploads to their archives"""
    id = db.Column(db.INT, primary_key=True)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    submission_id = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)


class Distros(db.Model):
    """Maps uploads to their distros"""
    id = db.Column(db.INT, primary_key=True)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    submission_id = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)


class File(db.Model):
    """Represents a single uploaded file"""
    id = db.Column(db.INT, primary_key=True)
    submission_id = db.Column(db.INT, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    path = db.Column(db.VARCHAR(255), nullable=False)

    @property
    def full_path(self):
        return os.path.join(self.submission.full_path, self.path)

    def preprocess(self, preprocessors):
        """Returns a list of (file, start, end, type, value) tuples created
        using a.  pygments lexer. The lexer is determined by looking
        first at file name then at file contents. If neither
        determines a lexer, a plain text lexer is used. The `type` in
        the output tuple is a pygments Token type.
        """
        file_path = self.full_path
        with open(file_path, "r")  as file:
            text = file.read()

        # get lexer for this file type
        try:
            lexer = pygments.lexers.get_lexer_for_filename(file_path)
        except pygments.util.ClassNotFound:
            try:
                lexer = pygments.lexers.guess_lexer(text)
            except pygments.util.ClassNotFound:
                lexer = pygments.lexers.special.TextLexer()

        # tokenize file into (start, type, value) tuples
        tokens = list(lexer.get_tokens_unprocessed(text))

        # add file and end index to create Tokens
        tokens.append((len(text),))
        tokens = [Token(start=tokens[i][0], stop=tokens[i+1][0],
                        type=tokens[i][1], val=tokens[i][2])
                  for i in range(len(tokens) - 1)]

        # run preprocessors
        for pp in preprocessors:
            tokens = pp(tokens)
        return list(tokens)



class Pass(db.Model):
    """Represents a run of a preprocessing and fingerprinting
    configuration for on an upload"""
    id = db.Column(db.INT, primary_key=True)
    # TODO: make config rich enough to re-run pass
    config = db.Column(db.VARCHAR(255), nullable=False)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    matches = db.relationship("Match", backref="processor")

    @property
    def failed(self):
        return AsyncResult(str(self.id)).failed()

    @property
    def ready(self):
        return AsyncResult(str(self.id)).ready()


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


@app.route("/api/", methods=["POST"])
def upload_api():
    id = upload()
    return jsonify(id)


@app.route("/api/<uuid:id>/delete", methods=["POST"])
def delete_files_api():
    # TODO: only let original uploader delete upload
    abort(501) # not implemented


@app.route("/api/<uuid:id>/submissions", methods=["GET"])
def get_submissions_api(id):
    upload = Upload.query.filter_by(uuid=id).first_or_404()
    return jsonify({f"{s.id}": s.path for s in upload.submissions})


@app.route("/api/<uuid:id>/pass", methods=["POST"])
def create_pass_api(id):
    pass_id = create_pass(id)
    return jsonify(pass_id)


@app.route("/api/<uuid:id>/pass", methods=["GET"])
def get_pass_api(id):
    pass_id = request.args.get("id")
    if pass_id is None:
        abort(400) # bad request

    p = Pass.query.get(pass_id)
    if p is None or p.upload.uuid != str(id):
        abort(400) # bad request

    if p.failed:
        abort(500) # server error
    elif not p.ready:
        return ('"pending"', 202) # accepted

    # task ready, get results
    return jsonify([
        {"a": m.sub_a, "b": m.sub_b, "score": m.score} for m in p.matches
    ])


@app.route("/api/<uuid:id>/compare", methods=["GET"])
def compare_api(id):
    submissions = validate_submission_args(id)
    files = compare(*submissions)
    data = tuple(
        [
            {
                "file": file.path,
                "fragments": [
                    {"text": frag.text, "groups": frag.groups}
                    for frag in fragments
                ]
            }
            for file, fragments in sub.items()
        ]
        for sub in files
    )
    return jsonify(data)


@app.route("/", methods=["GET", "POST"])
def upload_ui():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        id = upload()
        return redirect(url_for("results_ui", id=id))


@app.route("/<uuid:id>")
def results_ui(id):
    upload = Upload.query.filter_by(uuid=id).first_or_404()
    passes = [{"id": p.id, "name": p.config} for p in upload.passes]
    subs = {f"{s.id}": s.path for s in upload.all_submissions}
    return render_template("results.html", id=id, subs=subs, passes=passes)


@app.route("/<uuid:id>/pass", methods=["GET", "POST"])
def pass_ui(id):
    if request.method == "GET":
        return render_template("add_pass.html", id=id)
    elif request.method == "POST":
        create_pass(id)
        return redirect(f"/{id}")
        pass


@app.route("/<uuid:id>/compare", methods=["GET"])
def compare_ui(id):
    sub_a, sub_b = validate_submission_args(id)
    files_a, files_b = compare(sub_a, sub_b)
    passes = Upload.query.filter_by(uuid=str(id)).first().passes

    def make_sorted(files):
        files = {File.query.get(file).path: frags
                 for file, frags in files.items()}
        return sorted(files.items(), key=lambda f: f[0])

    return render_template("compare.html",
                           sub_a=sub_a.path,
                           sub_b=sub_b.path,
                           files_a=make_sorted(files_a),
                           files_b=make_sorted(files_b),
                           passes=passes)


def upload():
    # Check for files
    if not request.files.getlist("submissions"):
        abort(make_response(jsonify(error="missing submissions"), 400))

    # Unique parent
    upload = Upload()
    upload.uuid = id = str(uuid.uuid4())
    parent = upload.full_path
    try:
        os.mkdir(parent)
    except FileExistsError:
        abort(500)

    # Save submissions
    submission_dir = upload.submission_dir
    os.mkdir(submission_dir)
    for file in request.files.getlist("submissions"):
        save(file, submission_dir)

    # Save distros, if any
    if request.files.getlist("distros"):
        distro_dir = upload.distro_dir
        os.mkdir(distro_dir)
        for file in request.files.getlist("distros"):
            save(file, distro_dir)
    else:
        distro_dir = None

    # Save archives, if any
    if request.files.getlist("archives"):
        archive_dir = upload.archive_dir
        os.mkdir(archive_dir)
        for file in request.files.getlist("archives"):
            save(file, archives_dir)
    else:
        archive_dir = None

    distro = walk(distro_dir) if distro_dir else []
    submissions = walk_submissions(submission_dir)
    archives = walk_submissions(archive_dir) if archive_dir else []

    # (submission, association table) pairs
    subs = [(distro, Distros)] + \
        [(s, Submissions) for s in submissions] + \
        [(a, Archives) for a in archives]

    # create submission, file db objects
    for sub, Assoc in subs:
        if len(sub) == 0:
            continue

        s = Submission()
        sub_path = submission_path(sub)
        s.path = os.path.relpath(sub_path, parent)
        upload.all_submissions.append(s)

        for file in sub:
            f = File()
            f.path = os.path.relpath(file, sub_path)
            s.files.append(f)

        db.session.add(s)
        db.session.commit()

        a = Assoc()
        a.upload_id = upload.id
        a.submission_id = s.id
        db.session.add(a)

    db.session.add(upload)
    db.session.commit()

    return id


def create_pass(id):
    upload = Upload.query.filter_by(uuid=id).first_or_404()
    if request.form.get("config") is None:
        abort(400)

    # validate configuration
    if request.form.get("config") not in ["strip_ws", "strip_all"]:
        abort(400)

    # create pass object
    p = Pass()
    p.config = request.form.get("config")
    upload.passes.append(p)
    db.session.commit()

    # run pass asynchronously
    run_pass.apply_async(task_id=str(p.id))
    return p.id


@celery.task(bind=True)
def run_pass(self):
    p = Pass.query.get(int(self.request.id))

    # find directories where files were saved
    submission_dir = p.upload.submission_dir
    archive_dir = p.upload.archive_dir
    distro_dir = p.upload.distro_dir

    # get submission lists
    submissions = walk_submissions(submission_dir)
    distros = walk(distro_dir) if os.path.exists(distro_dir) else []
    archives = walk_submissions(archive_dir) if os.path.exists(archive_dir) else []

    # get pass components
    # TODO: make this user-configurable
    preprocessors, comparator = DEFAULT_CONFIG[p.config]

    sub_index = comparator.empty_index()
    archive_index = comparator.empty_index()

    # add submissions to left and right side
    print("processing submissions")
    for sub in p.upload.submissions:
        for f in sub.files:
            file_index = comparator.index(f.id, f.submission_id, f.preprocess(preprocessors))
            sub_index += file_index
            archive_index += file_index

    # add archives to right side only
    print("processing archives")
    for sub in p.upload.archives:
        for f in sub.files:
            archive_index += comparator.index(f.id, f.submission_id, f.preprocess(preprocessors))

    # remove distro from both sides
    print("processing distro")
    if p.upload.distro:
        for f in p.upload.distro.files:
            file_index = comparator.index(f.id, f.submission_id, f.preprocess(preprocessors))
            sub_index -= file_index
            archive_index -= file_index

    # Storen results in db
    print("Performing comparison")
    for match in sub_index.compare(archive_index, keep_spans=False):
        m = Match()
        m.sub_a = match.a
        m.sub_b = match.b
        m.score = match.score
        p.matches.append(m)

    db.session.add(p)
    db.session.commit()


def validate_submission_args(id):
    """Validate `a` and `b` request args with given upload id. Return
    submissions or abort.
    """
    a = request.args.get("a")
    b = request.args.get("b")
    if a is None or b is None or not a.isdigit() or not b.isdigit() or \
       int(a) >= int(b):
        abort(400)

    # check that submissions are from this upload
    sub_a = Submission.query.get(a)
    sub_b = Submission.query.get(b)
    if sub_a is None or sub_b is None or \
       sub_a.upload.uuid != str(id) or sub_b.upload.uuid != str(id):
        abort(400)

    return sub_a, sub_b


def compare(sub_a, sub_b):
    """Take two submissions and return a tuple of dicts mapping files to
    lists of Fragments.  The id of `sub_a` must be less than that of
    `sub_b`.
    """
    distro = sub_a.upload.distro

    # map pass ids to MatchResults
    results = {}

    for p in sub_a.upload.passes:
        preprocessors, comparator = DEFAULT_CONFIG[p.config]

        distro_files = p.upload.distro.files if distro else []

        # keep tokens around for expanding spans
        tokens = {f.id: f.preprocess(preprocessors)
                  for f in sub_a.files + sub_b.files + distro_files}

        # process files
        a_index = comparator.empty_index()
        b_index = comparator.empty_index()
        distro_index = comparator.empty_index()
        for files, index in [(sub_a.files, a_index),
                             (sub_b.files, b_index),
                             (distro_files, distro_index)]:
            for f in files:
                index += comparator.index(f.id, f.submission_id, tokens[f.id], complete=True)

        # perform comparisons
        matches = a_index.compare(b_index)
        if matches:
            matches = expand_spans(matches[0], tokens)
        else:
            # no matches, create empty MatchResult to hold distro code
            matches = MatchResult(sub_a.id, sub_b.id, {})
        if distro:
            # add expanded distro spans to match as group "distro"
            for index in a_index, b_index:
                distro_match = distro_index.compare(index)
                if distro_match:
                    distro_match = expand_spans(distro_match[0], tokens)
                    distro_spans = [span
                                    for spans in distro_match.spans.values()
                                    for span in spans
                                    if File.query.get(span.file).submission_id != distro.id]
                    matches.spans.setdefault("distro", []).extend(distro_spans)

        results[p.id] = matches

    return flatten_spans(results)


def expand_spans(match, tokens):
    """Returns a new MatchResult with maximally expanded spans.

    match - the MatchResult containing spans to expand
    tokens - a dict mapping files to lists of their tokens
    """
    # lazily map files to lists of token start indices
    start_cache = {}

    # binary search to find index of token with given start
    def get_index(file, start):
        starts = start_cache.get(file)
        if starts is None:
            starts = [t.start for t in tokens[file]]
            start_cache[file] = starts
        return bisect.bisect_left(starts, start)

    new_spans = {}
    for group_id, spans in match.spans.items():
        # if there exists an expanded group
        # for which all current spans are contained
        # in some expanded span, then skip this group
        if any(all(any(span.file == other.file and \
                       span.start >= other.start and \
                       span.stop <= other.stop
                       for other in expanded)
                   for span in spans)
               for expanded in new_spans.values()):
            continue
        # first, last index into file's tokens for each span
        print(spans)
        indices = {span: (get_index(span.file, span.start),
                          get_index(span.file, span.stop) - 1)
                   for span in spans}

        while True:
            changed = False
            # find previous and next tokens for each span
            prevs = set(tokens[span.file][first - 1].val if first > 0 else None
                        for span, (first, last) in indices.items())
            nexts = set((tokens[span.file][last + 1].val
                         if last + 1 < len(tokens[span.file]) else None)
                        for span, (first, last) in indices.items())

            # expand front of spans
            if len(prevs) == 1 and prevs.pop() is not None:
                changed = True
                indices = {span: (first - 1, last)
                           for span, (first, last) in indices.items()}
                # expand back of spans
            if len(nexts) == 1 and nexts.pop() is not None:
                changed = True
                indices = {span: (start, stop + 1)
                           for span, (start, stop) in indices.items()}
            if not changed:
                break

        new_spans[group_id] = [Span(span.file,
                                    tokens[span.file][first].start,
                                    tokens[span.file][last].stop)
                               for span, (first, last) in indices.items()]
    return MatchResult(match.a, match.b, match.score, new_spans)


def flatten_spans(matches):
    """Return a pair of dicts mapping Files to lists of Fragments. Each
    list of Fragments is the fragmented contents of an entire file.

    match - a dict mapping pass IDs to MatchResults
    """
    # separate spans by submission
    a_spans = {}
    b_spans = {}
    for pass_id, match in matches.items():
        for group, spans in match.spans.items():
            for span in spans:
                if File.query.get(span.file).submission_id == match.a:
                    spans = a_spans
                elif File.query.get(span.file).submission_id == match.b:
                    spans = b_spans
                else:
                    assert false, "Span from unknown submission in match"
                spans.setdefault(pass_id, {}) \
                    .setdefault(group, []) \
                    .append(span)

    a_results = {}
    b_results = {}
    for spans, results in (a_spans, a_results), (b_spans, b_results):
        # separate by file, move pass_id and group into tuple
        by_file = {}
        for pass_id, spans in spans.items():
            for group, spans in spans.items():
                for span in spans:
                    entry = by_file.setdefault(span.file, [])
                    entry.append((span, pass_id, group))

        for file, span_data in by_file.items():
            # iterate through text, creating list of Fragments
            file_results = []
            span_data.sort(key=lambda s: s[0].start)
            with open(File.query.get(file).full_path, "r") as f:
                text = f.read()
            current_spans = []
            current_text = []

            def create_frag():
                groups = {}
                for span, pass_id, group in current_spans:
                    groups.setdefault(pass_id, []).append(group)
                    if "distro" in groups[pass_id]:
                        groups[pass_id] = ["distro"]
                file_results.append(Fragment(groups, "".join(current_text)))

            for i, c in enumerate(text):
                # calculate new current groups
                new_spans = [(span, pass_id, group)
                             for span, pass_id, group in current_spans
                             if span.stop > i]
                while span_data and span_data[0][0].start == i:
                    new_spans.append(span_data.pop(0))

                # emit fragment if span would end or start
                if new_spans != current_spans:
                    create_frag()
                    current_text = []
                current_spans = new_spans
                current_text.append(c)

            # final fragment, possibly empty
            create_frag()
            results[file] = file_results

    return a_results, b_results
