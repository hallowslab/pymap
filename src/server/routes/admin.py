from flask import current_app, jsonify, request
from flask_praetorian import roles_accepted

# Core and Flask app
from server.extensions import db, guard

# Models
from server.models.tasks import CeleryTask
from server.routes.apiv2 import apiv2_blueprint


@apiv2_blueprint.route("/api/v2/admin/tasks", methods=["GET"])
@roles_accepted("admin")
def get_tasks_v2():
    # Get all tasks
    token = guard.read_token_from_header()
    print(guard.extract_jwt_token(token).get("id"))
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


@apiv2_blueprint.route("/api/v2/admin/delete-task", methods=["GET", "POST"])
@roles_accepted("admin")
def delete_task():
    task_id = request.args.get("id", None)
    if not task_id:
        return (jsonify(message="You need to provide a task ID"), 400)
    return ("Not implemented", 418)


@apiv2_blueprint.route("/api/v2/admin/archive-task", methods=["GET", "POST"])
@roles_accepted("admin")
def archive_task():
    task_id = request.args.get("id", None)
    if not task_id:
        return (jsonify(message="You need to provide a task ID"), 400)
    return ("Not implemented", 418)
