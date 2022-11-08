from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS
import json
from flask.logging import default_handler
from celery import Celery
import sys

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

    app.logger.addHandler(default_handler)

    # set config
    if "--debug" in argv:
        app.config.from_file("config.dev.json", load=json.load)
        CORS(apiv1_blueprint)
    else:
        app.config.from_file("config.json", load=json.load)

    # initialize DB after loading config
    db.init_app(app)

    # register blueprints
    if not app.config.get("HEADLESS", False):
        app.register_blueprint(main_blueprint)
    app.register_blueprint(apiv1_blueprint)

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
