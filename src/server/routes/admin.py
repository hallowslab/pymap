import os
import shutil
from typing import List
from flask import current_app, jsonify, request, Blueprint
from flask_praetorian import roles_accepted, current_user

# Core and Flask app
from server.extensions import db
from server.utils import log_redis
from server.tasks import celery_app
# Models
from server.models.tasks import CeleryTask

admin_blueprint = Blueprint("admin", __name__)


@admin_blueprint.route("/api/v2/admin/delete-tasks", methods=["POST"])
@roles_accepted("admin")
def delete_task():
    content = request.json
    ids: List[str] = content.get("task_ids")
    user = current_user()
    extra_message = ""
    processed = {}
    if not ids:
        return (jsonify(error=400, message="You need to specify task id"), 400)
    for task_id in ids:
        log_redis(user.username, f"User requested deletion of task with ID: {task_id}")
        current_app.logger.info(
            user.username, f"User requested deletion of task with ID: {task_id}"
        )
        try:
            task = CeleryTask.query.filter_by(task_id=task_id).first()
            if not task:
                processed[task_id] = f"Task with ID: {task_id} was not found"
                continue
            task_path = task.log_path
            db.session.delete(task)
            db.session.commit()
            if not os.path.isdir(task_path):
                extra_message = f"Directory does not exist: {task.log_path}"
            else:
                shutil.rmtree(task.log_path)
                extra_message = f"Removed files from {task.log_path}"
            final_message = f"Deleted task with ID: {task_id}, {extra_message}"
            processed[task_id] = final_message
            current_app.logger.info(final_message)
        except Exception as e:
            current_app.logger.critical(
                "Unhandled exception: %s", e.__str__(), exc_info=1
            )
            processed[task_id] = "Unhandled exception: %s", e.__str__()
    return (jsonify(message=processed), 200)


@admin_blueprint.route("/api/v2/admin/archive-tasks", methods=["POST"])
@roles_accepted("admin", "operator")
def archive_task():
    content = request.json
    ids: List[str] = content.get("task_ids")
    user = current_user()
    extra_message = ""
    processed = {}
    if not ids:
        return (jsonify(error=400, message="You need to specify task id"), 400)
    for task_id in ids:
        log_redis(user.username, f"User requested archival of task with ID: {task_id}")
        current_app.logger.info(f"User requested archival of task with ID: {task_id}")
        new_path = os.path.join(
            current_app.config.get("LOG_DIRECTORY"), f"archive/{task_id}"
        )
        try:
            task = CeleryTask.query.filter_by(task_id=task_id).first()
            if not task:
                processed[task_id] = f"Task with ID: {task_id} was not found"
                continue
            task_path = task.log_path
            if not os.path.isdir(task_path):
                extra_message = f"Directory does not exist: {task_path}"
            else:
                shutil.move(task_path, new_path)
                task.log_path = new_path
                extra_message = f"Moved files from {task.log_path} to {new_path}"
            task.archived = True
            db.session.commit()
            final_message = f"Archived task with ID: {task_id}, {extra_message}"
            processed[task_id] = final_message
            current_app.logger.info(final_message)
        except Exception as e:
            current_app.logger.critical(
                "Unhandled exception: %s", e.__str__(), exc_info=1
            )
            processed[task_id] = "Unhandled exception: %s", e.__str__()
    return (jsonify(message=processed), 200)

@admin_blueprint.route("/api/v2/admin/cancel/<task_id>")
@roles_accepted("admin", "operator")
def cancel_task(task_id):
    user = current_user()
    log_redis(user.username, f"Requested cancellation of task with ID: {task_id}")
    current_app.logger.info(f"Requested cancellation of task with ID: {task_id}")
    try:
        celery_app.control.revoke(task_id)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return (jsonify(error=400, message=e.__str__()), 400)