from os import mkdir
from os.path import isdir
from flask import Blueprint, jsonify, request, url_for, current_app, abort, redirect
from flask_praetorian import auth_required

# Core and Flask
from core.pymap_core import ScriptGenerator
from server import db, guard
from server.tasks import call_system

# Models
from server.models.users import User
from server.models.tasks import CeleryTask


apiv2_blueprint = Blueprint("apiV2", __name__)


@apiv2_blueprint.route("/api/v2/sync", methods=["POST"])
def sync_v2():
    content = request.json
    # TODO: Strip out passwords before logging data
    # current_app.logger.debug("Parsing the following json data:\n %s", content)
    source = content.get("source")
    dest = content.get("destination")
    creds = content.get("input")
    extra_args = content.get("extra_args", None)
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
def get_tasks_v2():
    # Get all tasks
    try:
        query = [t.__dict__ for t in db.session.query(CeleryTask).all()]
        all_tasks = []
        for t in query:
            all_tasks.append({k: v for k, v in t.items() if k != "_sa_instance_state"})
        # TODO: Handle errors, or just return the array with tasks: or error:
        return (jsonify({"tasks": all_tasks}), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return jsonify({"error": e.__class__.__name__, "message": e.__str__()}, 400)


@apiv2_blueprint.route("/api/v2/login", methods=["POST"])
def do_login():
    identifier = request.json.get("identifier", None)
    password = request.json.get("password", None)
    if identifier is None or password is None:
        abort(401)

    user = User.query.filter_by(username=identifier).first()
    email = User.query.filter_by(email=identifier).first()
    identifier = email.username if user is None else user
    user = guard.authenticate(identifier, password)
    ret = {"access_token": guard.encode_jwt_token(user)}
    return (jsonify(ret), 200)


@apiv2_blueprint.route("/api/v2/logout", methods=["POST"])
def logout():
    return redirect("/")


@apiv2_blueprint.route("/api/v2/register", methods=["POST"])
@auth_required
def register_user():
    content = request.json
    username = content.get("username")
    email = content.get("email")
    password = content.get("password")

    user_exists = User.query.filter_by(username=username).first() is not None
    email_exists = User.query.filter_by(email=email).first() is not None

    if user_exists or email_exists:
        abort(409)

    hashed_password = guard.hash_password(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify(
        {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }
    )
