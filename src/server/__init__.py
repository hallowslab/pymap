from datetime import timedelta
import secrets
import sys
import json
from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS
from flask_praetorian import Praetorian
from flask_migrate import Migrate
from celery import Celery
import redis

from server.models import db, users

ACCESS_EXPIRES = timedelta(minutes=10)


guard = Praetorian()

jwt_redis_blocklist = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)


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
    from server.routes.user_management import user_manager_blueprint

    app.logger.addHandler(default_handler)

    # set config
    if "--debug" in argv:
        app.config.from_file("config.dev.json", load=json.load)
        CORS(apiv1_blueprint)
    else:
        app.config.from_file("config.json", load=json.load)
    if app.config.get("JWT_SECRET_KEY", "") == "":
        app.config["JWT_SECRET_KEY"] = secrets.SystemRandom()
    if app.config.get("SECRET_KEY", "") == "":
        app.config["SECRET_KEY"] = secrets.SystemRandom()

    # Initialize DB after loading config
    db.init_app(app)

    # Initialize the flask-praetorian instance for the app
    guard.init_app(app, user_class=users.User)

    # Flask migrate
    Migrate(app, db)

    # register blueprints
    if not app.config.get("HEADLESS", False):
        app.register_blueprint(main_blueprint)
    app.register_blueprint(apiv1_blueprint)
    app.register_blueprint(apiv2_blueprint)
    app.register_blueprint(user_manager_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})
    return app


argv = sys.argv[1:]


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
