import flask_migrate
import os
import tarfile
import uuid

from flask import Flask, Response, abort, jsonify, make_response, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from raven.contrib.flask import Sentry
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
    """TODO"""
    result = AsyncResult(id)
    print(f"Task status: {result.state}")
    if result.state == "FAILURE":
        print(result.result)
    elif result.state == "SUCCESS":
        with open(result.result, "r") as f:
            return Response(f.read(), mimetype="text/json")
    return jsonify(walk(os.path.join(gettempdir(), str(id))))
