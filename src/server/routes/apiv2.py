from os import mkdir
from os.path import isdir
from flask import Blueprint, current_app, request, url_for
from flask_praetorian import roles_accepted, auth_required, current_user_id

# Core and Flask app
from core.pymap_core import ScriptGenerator
from server.extensions import db
from server.tasks import call_system
from server.utils import log_redis

# Models
from server.models.tasks import CeleryTask
from server.models.users import User

apiv2_blueprint = Blueprint("apiV2", __name__)


@apiv2_blueprint.route("/api/v2/heartbeat", methods=["GET"])
@auth_required
def heartbeat():
    id: int = current_user_id()
    user = User.query.filter_by(id=id).first_or_404()
    return {"message": user.username}, 200


@apiv2_blueprint.route("/api/v2/sync", methods=["POST"])
@roles_accepted("operator", "admin")
def sync_v2():
    log_directory = current_app.config.get("LOG_DIRECTORY")
    id: int = current_user_id()
    user = User.query.filter_by(id=id).first_or_404()
    content = request.json
    # TODO: Strip out passwords before logging data
    # current_app.logger.debug("Parsing the following json data:\n %s", content)
    source: str = content.get("source")
    dest: str = content.get("destination")
    creds: str = content.get("input")
    extra_args = content.get("extra_args")
    extra_args = None if extra_args.strip() == "" else extra_args
    current_app.logger.debug(
        f"Extra Arguments: {extra_args}, Extra arguments type: {type(extra_args)}"
    )
    log_redis(
        user.username,
        f"Sent sync request from {source} to {dest}, with additional parameters: {extra_args}",
    )
    gen = ScriptGenerator(
        source, dest, creds=creds, extra_args=extra_args, config=current_app.config
    )
    content = gen.process_string()
    # TODO: Strip out passwords before logging commands
    """current_app.logger.debug(
        "Received the following output from generator:\n %s", content
    )"""
    task = call_system.delay(content)
    ctask = CeleryTask(
        source=source,
        destination=dest,
        log_path=f"{log_directory}/{task.id}",
        task_id=task.id,
        n_accounts=len(content),
        owner_username=user.username,
    )
    db.session.add(ctask)
    db.session.commit()
    if not isdir(f"{log_directory}/{task.id}"):
        mkdir(f"{log_directory}/{task.id}")
    current_app.logger.info("Starting background task with ID: %s", task.id)
    return {
        "location": url_for("tasks.task_status", task_id=task.id),
        "taskID": task.id,
    }, 202
