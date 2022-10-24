import secrets
import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS
import json
from flask.logging import default_handler
from celery import Celery
import sys

from server.extensions import jwt

db = SQLAlchemy()

argv = sys.argv[1:]


def create_flask_app(script_info=None):

    # instantiate the app
    app = Flask(
        __name__,
        template_folder="../build/templates",
        static_folder="../build/static",
    )

    # import blueprints
    from server.routes.views import main_blueprint
    from server.routes.apiv1 import apiv1_blueprint
    from server.routes.apiv2 import apiv2_blueprint

    app.logger.addHandler(default_handler)

    # set config
    if "--debug" in argv:
        app.config.from_file("config.dev.json", load=json.load)
        CORS(apiv1_blueprint)
    else:
        app.config.from_file("config.json", load=json.load)
    if app.config.get("JWT_SECRET_KEY", "") == "":
        app.config["JWT_SECRET_KEY"] = secrets.SystemRandom()
    # TODO: Move to config like above
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']

    # Initialize jwt
    jwt.init_app(app)

    # initialize DB after loading config
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # register blueprints
    if not app.config.get("HEADLESS", False):
        app.register_blueprint(main_blueprint)
    app.register_blueprint(apiv1_blueprint)
    app.register_blueprint(apiv2_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})
    return app


def create_celery_app():
    # configure celery
    celery_app = Celery(__name__)
    params = ["broker_url", "result_backend"]
    config = {}
    if "DEBUG" in argv:
        with open("server/config.dev.json") as fh:
            config = json.load(fh)
    with open("server/config.json") as fh:
        config = json.load(fh)
    config = config["CELERY"]
    for item in params:
        if item in config.keys():
            celery_app.conf[item] = config.get(item)
    return celery_app
