import os
import shutil
from typing import List
from flask import current_app, request, Blueprint
from flask_praetorian import roles_accepted, current_user
from celery.result import AsyncResult

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
        return {"error": "You need to specify task id"}, 400
    for task_id in ids:
        log_redis(user.username, f"User requested deletion of task with ID: {task_id}")
        current_app.logger.info(
            f"User {user.username} requested deletion of task with ID: {task_id}"
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
        except Exception as e:
            current_app.logger.critical(
                "Unhandled exception: %s", e.__str__(), exc_info=1
            )
            processed[task_id] = "Unhandled exception: %s", e.__str__()
    current_app.logger.info(
        "Processed deletion request from %s, %s", user.username, processed
    )
    return {"message": processed}, 200


@admin_blueprint.route("/api/v2/admin/archive-tasks", methods=["POST"])
@roles_accepted("admin", "operator")
def archive_task():
    status = 200
    content = request.json
    ids: List[str] = content.get("task_ids")
    user = current_user()
    extra_message = ""
    processed = {}
    if not ids:
        return {"error": "You need to specify task id"}, 400
    for task_id in ids:
        log_redis(user.username, f"User requested archival of task with ID: {task_id}")
        current_app.logger.info(
            f"User {user.username} requested archival of task with ID: {task_id}"
        )
        new_path = os.path.join(
            current_app.config.get("LOG_DIRECTORY"), f"archive/{task_id}"
        )
        try:
            task = CeleryTask.query.filter_by(task_id=task_id).first()
            if not task:
                processed[task_id] = f"Task with ID: {task_id} was not found"
                status = 207
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
        except Exception as e:
            current_app.logger.critical(
                "Unhandled exception: %s", e.__str__(), exc_info=1
            )
            processed[task_id] = "Unhandled exception: %s", e.__str__()
            status = 207
    current_app.logger.info(
        "Processed archival request from %s, %s", user.username, processed
    )
    return {"message": processed}, status


@admin_blueprint.route("/api/v2/admin/cancel-tasks")
@roles_accepted("admin", "operator")
def cancel_task(task_id):
    status = 200
    content = request.json
    user = current_user()
    ids: List[str] = content.get("task_ids")
    processed = {}
    if not ids:
        return {"error": "You need to specify task id"}, 400
    for task_id in ids:
        log_redis(user.username, f"Requested cancellation of task with ID: {task_id}")
        current_app.logger.info(
            f"User {user.username} requested cancellation of task with ID: {task_id}"
        )
        try:
            task = CeleryTask.query.filter_by(task_id=task_id).first()
            result = AsyncResult(task_id, app=celery_app)
            if not task:
                processed[task_id] = f"Task with ID: {task_id} was not found"
                status = 207
                continue
            elif result.state == "SUCCESS":
                processed[
                    task_id
                ] = f"Task with ID: {task_id} has already finished executing"
                status = 207
                continue
            else:
                celery_app.control.revoke(task_id, terminate=True)
                processed[task_id] = f"Task with ID: {task_id} was cancelled"
        except Exception as e:
            current_app.logger.critical(
                "Unhandled exception: %s", e.__str__(), exc_info=1
            )
            processed[task_id] = "Unhandled exception: %s", e.__str__()
            status = 207
            continue
    current_app.logger.info(
        "Processed cancelation request from %s, %s", user.username, processed
    )
    return {"message": processed}, status
