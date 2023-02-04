import os
import shutil
from flask import current_app, jsonify, request
from flask_praetorian import roles_accepted

# Core and Flask app
from server.extensions import db, guard

# Models
from server.models.tasks import CeleryTask
from server.routes.apiv2 import apiv2_blueprint


@apiv2_blueprint.route("/api/v2/admin/delete-task", methods=["POST"])
@roles_accepted("admin")
def delete_task():
    task_id = request.args.get("id", None)
    if not task_id:
        return jsonify(error="You need to specify task id")
    try:
        task = CeleryTask.query.filter_by(id=task_id).first_or_404()
        task_path = task.log_path
        db.session.delete(task)
        db.session.commit()
        extra_message = f"Failed to remove files from {task.log_path}"
        if os.path.isdir(task_path):
            extra_message = f"Removed files from {task.log_path}"
            shutil.rmtree(task.log_path)
        return (jsonify(message=f"Deleted task with ID: {task_id}, {extra_message}"), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return jsonify({"error": e.__class__.__name__, "message": e.__str__()}, 400)
    

@apiv2_blueprint.route("/api/v2/admin/archive-task", methods=["POST"])
@roles_accepted("admin")
def archive_task():
    task_id = request.args.get("id", None)
    new_path = os.path.join(current_app.config.get("LOG_DIRECTORY"), f"archive/{task_id}")
    if not task_id:
        return jsonify(error="You need to specify task id")
    try:
        task = CeleryTask.query.filter_by(id=task_id).first_or_404()
        task_path = task.log_path
        if os.path.isdir(task_path):
            extra_message = f"Moving file from {task.log_path} to {new_path}"
            shutil.move(task.log_path, new_path)
        return (jsonify(message=f"Archived task with ID: {task_id}, {extra_message}"), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return jsonify({"error": e.__class__.__name__, "message": e.__str__()}, 400)
