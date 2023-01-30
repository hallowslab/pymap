from os import mkdir
from os.path import isdir
from flask import Blueprint, current_app, jsonify, request, url_for
from flask_praetorian import roles_accepted, auth_required

# Core and Flask app
from core.pymap_core import ScriptGenerator
from server import db, guard
from server.tasks import call_system

# Models
from server.models.tasks import CeleryTask
from server.models.users import User

apiv2_blueprint = Blueprint("apiV2", __name__)


@apiv2_blueprint.route("/api/v2/sync", methods=["POST"])
@roles_accepted("operator", "admin")
def sync_v2():
    id = guard.extract_jwt_token(guard.read_token_from_header()).get("id")
    user = User.query.filter_by(id=id).first_or_404()
    content = request.json
    # TODO: Strip out passwords before logging data
    # current_app.logger.debug("Parsing the following json data:\n %s", content)
    source = content.get("source")
    dest = content.get("destination")
    creds = content.get("input")
    extra_args = content.get("extra_args", "")
    extra_args = None if extra_args.strip() == "" else extra_args
    current_app.logger.debug(
        f"Extra Arguments: {extra_args}, Extra arguments type: {type(extra_args)}"
    )
    gen = ScriptGenerator(source, dest, creds, extra_args, config=current_app.config)
    content = gen.process(mode="api")
    # TODO: Strip out passwords before logging commands
    """current_app.logger.debug(
        "Received the following output from generator:\n %s", content
    )"""
    task = call_system.delay(content)
    ctask = CeleryTask(
        source=source,
        destination=dest,
        log_path=f"/var/log/pymap/{task.id}",
        task_id=task.id,
        n_accounts=len(content),
        domain=gen.domain,
        owner_id=id,
        owner_username=user.username
    )
    db.session.add(ctask)
    db.session.commit()
    if not isdir(f"/var/log/pymap/{task.id}"):
        mkdir(f"/var/log/pymap/{task.id}")
    current_app.logger.info("Starting background task with ID: %s", task.id)
    return (
        jsonify(
            {
                "location": url_for("apiV1.task_status", task_id=task.id),
                "taskID": task.id,
            }
        ),
        202,
    )

@apiv2_blueprint.route("/api/v2/tasks", methods=["GET"])
@auth_required
def get_tasks_v2():
    id = guard.extract_jwt_token(guard.read_token_from_header()).get("id")
    # Get all tasks
    try:
        query = CeleryTask.query.filter_by(owner_id=id).all()
        print(type(query))
        all_tasks = []
        for t in query:
            all_tasks.append({
                "id": t.id,
                "source": t.source,
                "destination": t.destination,
                "domain": t.domain,
                "n_accounts": t.n_accounts,
                "owner_id": t.owner_id
                })
        return (jsonify({"tasks": all_tasks}), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return jsonify({"error": e.__class__.__name__, "message": e.__str__()}, 400)


@apiv2_blueprint.route("/api/v2/heartbeat", methods=["GET"])
@auth_required
def heartbeat():
    id = guard.extract_jwt_token(guard.read_token_from_header()).get("id")
    user = User.query.filter_by(id=id).first_or_404()
    # Get all tasks
    return (jsonify({"message": user.username}), 200)
