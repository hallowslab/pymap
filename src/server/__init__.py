import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS
import json
from flask.logging import default_handler

db = SQLAlchemy()


def create_app(script_info=None):

    # instantiate the app
    app = Flask(
        __name__, template_folder="../build/templates", static_folder="../build/static",
    )

    # import blueprints
    from server.routes.views import main_blueprint
    from server.routes.apiv1 import apiv1_blueprint

    app.logger.addHandler(default_handler)

    # set config
    if os.getenv("FLASK_ENV") == "development":
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
