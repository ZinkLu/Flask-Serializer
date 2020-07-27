# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_serializer import FlaskSerializer

app = Flask(__name__)

DB_CLI = os.environ.get("DB_CLI", "postgresql")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_USER = os.environ.get("DB_USER")
DB_PWD = os.environ.get("DB_PWD")
DB_NAME = os.environ.get("DB_NAME")

SQLALCHEMY_DATABASE_URI = f'{DB_CLI}://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

print(SQLALCHEMY_DATABASE_URI)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)
session = db.session

fs = FlaskSerializer(app, strict=False)
