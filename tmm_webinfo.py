from flask import Flask, render_template
import os

from db_model import db

app = Flask(__name__)
app.config["DEBUG"] = True

if 'tmm_webinfo.db_hostname' in os.environ:
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
        username=os.environ['tmm_webinfo.db_user'],
        password=os.environ['tmm_webinfo.db_password'],
        hostname=os.environ['tmm_webinfo.db_hostname'],
        databasename=os.environ['tmm_webinfo.db_database'],
    )
else:
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.sqlite"

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route('/example')
def example():
    return render_template("example.html", title="Jinja and Flask")


@app.route('/')
def index():
    return render_template("index.html", title="Jinja and Flask")

