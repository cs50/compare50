import flask_migrate
import os
import tarfile
import uuid

from backports.shutil_which import which
from flask import Flask, abort, jsonify, make_response, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from raven.contrib.flask import Sentry
from tempfile import gettempdir, mkstemp
from werkzeug.utils import secure_filename

import patoolib

# Application
app = Flask(__name__)

# Monitoring
Sentry(app)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://{}:{}@{}/{}".format(
    os.environ["MYSQL_USERNAME"], os.environ["MYSQL_PASSWORD"], os.environ["MYSQL_HOST"], os.environ["MYSQL_DATABASE"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app, db)

# Enable UUID-based routes
FlaskUUID(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Supported archives, per https://github.com/wummel/patool
ARCHIVES = [".bz2", ".tar", ".tar.gz", ".tgz", ".zip", ".7z", ".xz"]

# Supported helper applications
HELPERS = {
    "7z": (".7z"),
    "compress": (".z"),
    "unrar": (".rar"),
    "xz": (".xz")
}
for progname, extensions in HELPERS.items():
    if which(progname):
        ARCHIVES.extend(extensions)


@app.before_first_request
def before_first_request():

    # Perform any migrates
    flask_migrate.upgrade()


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
        save(file, submissions)

    # Save distros, if any
    if request.files.getlist("distros"):
        distros = os.path.join(parent, "distros")
        os.mkdir(distros)
        for file in request.files.getlist("distros"):
            save(file, distros)

    # Save archives, if any
    if request.files.getlist("archives"):
        archives = os.path.join(parent, "archives")
        os.mkdir(archives)
        for file in request.files.getlist("archives"):
            save(file, archives)

    # TODO
    # results = compare(walk(files), walk(distros), walk(archives))

    # Redirect to results
    return redirect(url_for("results", id=id))


@app.route("/<uuid:id>")
def results(id):
    """TODO"""
    return jsonify(walk(os.path.join(gettempdir(), str(id))))


def save(file, dirpath):
    """Saves file at dirpath, extracting to identically named folder if archive."""
    filename = secure_filename(file.filename)
    path = os.path.join(dirpath, filename)
    if path.lower().endswith(tuple(ARCHIVES)):
        try:
            _, pathname = mkstemp(filename)
            file.save(pathname)
            os.mkdir(path)
            try:
                patoolib.extract_archive(pathname, outdir=path)
            except patoolib.util.PatoolError:
                abort(500) # TODO: pass helpful message
            os.remove(pathname)
        except Exception:
            abort(500) # TODO: pass helpful message
    else:
        file.save(path)


def walk(directory):
    """Walks directory recursively, returning sorted list of paths of files therein."""
    files = []
    for (dirpath, dirnames, filenames) in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(dirpath, filename))
    sorted(sorted(files), key=str.upper)
    return files
