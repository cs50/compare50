import flask_migrate
import os
import uuid

from flask import Flask, abort, redirect, render_template, request, send_from_directory, session, url_for
from flask.ext.uuid import FlaskUUID
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry
from tempfile import mkdtemp

# Routes
routes = []

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


@app.before_first_request
def before_first_request():

    # Perform any migrates
    flask_migrate.upgrade()


@app.route("/", methods=["GET"])
def get():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def post():
    pass
