import secrets
import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta
from typing import List
from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS
from flask_migrate import Migrate
from celery import Celery
from server.extensions import db, guard, redis_store
from server.models.users import User
from server.utils import REQUEST_FORMATTER

argv = sys.argv[1:]

# TODO: move to flask config
ACCESS_EXPIRES = timedelta(minutes=10)


def check_token_blacklisted(jti):
    token_in_redis = redis_store.get(jti)
    if token_in_redis is None:
        return False
    return True


def create_flask_app(config={}, script_info=None):

    _debug = True if "--debug" in argv else False
    # instantiate the app
    app = Flask(
        __name__,
        template_folder="../build/templates",
        static_folder="../build/static",
    )

    # import blueprints
    from server.routes.views import main_blueprint
    from server.routes.apiv2 import apiv2_blueprint
    from server.routes.tasks import tasks_blueprint
    from server.routes.user_management import user_manager_blueprint
    from server.routes.admin import admin_blueprint

    app.logger.addHandler(default_handler)

    # set config
    if _debug:
        app.config.from_file("config.dev.json", load=json.load)
        CORS(apiv2_blueprint)
        CORS(tasks_blueprint)
        CORS(user_manager_blueprint)
        CORS(admin_blueprint)
    elif len(config) > 0:
        app.config.from_mapping(config)
    else:
        app.config.from_file("config.json", load=json.load)
    if app.config.get("JWT_SECRET_KEY", "") == "":
        app.config["JWT_SECRET_KEY"] = str(secrets.token_hex(21))
    if app.config.get("SECRET_KEY", "") == "":
        app.config["SECRET_KEY"] = str(secrets.token_hex(21))

    # Create required directories
    logdir = app.config.get("LOG_DIRECTORY", "/var/log/pymap")
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    # Configure logging after importing config to access LOG_DIRECTORY
    log_name = f"{logdir}/pymap.log"
    file_handler = RotatingFileHandler(log_name, maxBytes=50000, backupCount=3)
    file_handler.setFormatter(REQUEST_FORMATTER)
    file_handler.setLevel(app.config.get("LOG_LEVEL", "INFO"))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(app.config.get("LOG_LEVEL", "INFO"))

    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    # Initialize DB after loading config
    db.init_app(app)

    # Flask migrate
    Migrate(app, db)

    # Initialize the flask-praetorian instance for the app
    # TODO: Find out why using flask migrate without this "with app.app_context():" raises the
    # Working outside of application context error only for praetorian
    # https://flask.palletsprojects.com/en/2.2.x/appcontext/#:~:text=RuntimeError%3A%20Working%20outside%20of%20application,app_context().
    with app.app_context():
        guard.init_app(app, user_class=User, is_blacklisted=check_token_blacklisted)

    # register blueprints
    if not app.config.get("HEADLESS", False):
        app.register_blueprint(main_blueprint)
    app.register_blueprint(apiv2_blueprint)
    app.register_blueprint(tasks_blueprint)
    app.register_blueprint(user_manager_blueprint)
    app.register_blueprint(admin_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})
    return app


def create_celery_app(options: List[str] = [""]):
    # Initialize celery
    celery_app = Celery(__name__)

    # Load the config
    config = {}
    if "--debug" in options or "DEBUG" in options:
        with open("server/config.dev.json") as fh:
            config = json.load(fh)
    else:
        with open("server/config.json") as fh:
            config = json.load(fh)

    # Grab the log directory
    LOG_DIR = config["LOG_DIRECTORY"]
    # Select the celery section
    config = config["CELERY"]
    # Append the log directory to the new dictionary
    config["LOG_DIRECTORY"] = LOG_DIR

    # loop trough the items and set the values manually
    for item in config:
        celery_app.conf[item] = config.get(item)

    return celery_app
