import flask_migrate
import json
import os
import tarfile
import uuid

from flask import Flask, Response, abort, jsonify, make_response, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from raven.contrib.flask import Sentry
from sqlalchemy.sql import func
from tempfile import gettempdir, mkstemp
from celery.result import AsyncResult

from tasks import compare_task
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


class Upload(db.Model):
    """Represents a particular batch of uploaded submissions"""
    id = db.Column(db.INT, primary_key=True)
    uuid = db.Column(db.CHAR(36), nullable=False, unique=True)
    created = db.Column(db.TIMESTAMP, nullable=False, default=func.now())
    passes = db.relationship("Pass", backref="upload")
    submissions = db.relationship("Submission", backref="upload")
    hashes = db.relationship("Hash", backref="upload")


class Pass(db.Model):
    """Represents a run of a preprocessing and fingerprinting
    configuration for on an upload"""
    id = db.Column(db.INT, primary_key=True)
    # TODO: make config rich enough to re-run pass
    config = db.Column(db.VARCHAR(255), nullable=False)
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)


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
    upload_id = db.Column(db.INT, db.ForeignKey("upload.id", ondelete="CASCADE"), nullable=False)
    fragments = db.relationship("Fragment", backref="hash")


class Fragment(db.Model):
    """Represents a particular section of text in a file"""
    id = db.Column(db.INT, primary_key=True)
    hash_id = db.Column(db.INT, db.ForeignKey("hash.id", ondelete="CASCADE"), nullable=False)
    file_id = db.Column(db.INT, db.ForeignKey("file.id", ondelete="CASCADE"), nullable=False)
    start = db.Column(db.INT, nullable=False)
    end = db.Column(db.INT, nullable=False)


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
        with open(result.result, "r") as f:
            info = json.load(f)
        return render_template("results.html", id=id, info=info)
    return jsonify(walk(os.path.join(gettempdir(), str(id))))

@app.route("/<uuid:id>/compare")
def compare(id):
    result = AsyncResult(id)
    if result.state != "SUCCESS":
        return redirect(f"/{id}")
    a = request.args.get("a")
    b = request.args.get("b")
    if a is None or b is None or not a.isdigit() or not b.isdigit():
        # TODO: error?
        return redirect(f"/{id}")
    with open(result.result, "r") as f:
        results = json.load(f)
        pair = [int(a), int(b)]
        for result in results["results"]:
            if result["subs"] == pair:
                return jsonify(result["passes"])
        # TOOD: error?
        return jsonify("error")
