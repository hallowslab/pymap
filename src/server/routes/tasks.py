from os import listdir
from os.path import isfile, join
from subprocess import TimeoutExpired, Popen, PIPE
from typing import Any, Dict
from flask import Blueprint, current_app, jsonify, request, send_file
from flask_praetorian import auth_required

# Core and Flask app
from server.extensions import guard
from server.tasks import call_system
from server.utils import get_logs_status

# Models
from server.models.tasks import CeleryTask
from server.models.users import User

tasks_blueprint = Blueprint("tasks", __name__)

# TODO: Move this to flask config
LOG_DIRECTORY = "/var/log/pymap"


@tasks_blueprint.route("/api/v2/tasks", methods=["GET"])
@auth_required
def get_tasks_v2():
    token: Dict[str, Any] = guard.extract_jwt_token(guard.read_token_from_header())
    roles: str = token.get("rls", "")
    id: int = token.get("id")
    # Get all tasks
    try:
        user = User.query.filter_by(id=id).first_or_404()
        query = (
            CeleryTask.query.filter_by(owner_username=user.username).all()
            if "admin" not in roles
            else CeleryTask.query.order_by(CeleryTask.owner_username).all()
        )
        all_tasks = []
        for t in query:
            all_tasks.append(
                {
                    "id": t.id,
                    "source": t.source,
                    "destination": t.destination,
                    "domain": t.domain,
                    "n_accounts": t.n_accounts,
                    "owner_username": t.owner_username,
                }
            )
        return (jsonify({"tasks": all_tasks}), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return jsonify({"error": e.__class__.__name__, "message": e.__str__()}, 400)


# TODO: This is not really being used atm
@tasks_blueprint.route("/api/v2/task-status/<task_id>", methods=["GET"])
def task_status(task_id):
    task = call_system.AsyncResult(task_id)
    response = {"Querying status": True}
    # Common states
    C_STATES = ["PROGRESS", "SUCCESS"]
    if task and task.info:
        if task.state == "PENDING":
            # job did not start yet
            response = {
                "state": task.state,
                "processing": task.info.get("processing", 0),
                "pending": task.info.get("pending", 0),
                "total": task.info.get("total", 1),
                "status": "Pending....",
            }
        elif task.state in C_STATES:
            response = {
                "state": task.state,
                "processing": task.info.get("processing", 0),
                "pending": task.info.get("pending", 0),
                "total": task.info.get("total", 1),
                "return_codes": task.info.get("return_codes", []),
                "status": task.info.get("status", ""),
            }
        elif task.state == "FAILURE":
            response = {
                "state": task.state,
                "processing": task.info.get("processing", 0),
                "pending": task.info.get("pending", 0),
                "total": task.info.get("total", 1),
                "return_codes": task.info.get("return_codes", []),
                "status": task.info.get("status", ""),
            }
            if "result" in task.info:
                response["result"] = task.info["result"]
        else:
            # something went wrong in the background job
            return {
                "state": task.state,
                "processing": task.info.get("processing", 0),
                "pending": task.info.get("pending", 0),
                "total": task.info.get("total", 1),
                "return_codes": task.info.get("return_codes", []),
                "status": str(task.info),  # this is the exception raised
            }
        return response
    else:
        return {
            "state": "Unknown",
            "processing": 0,
            "pending": 0,
            "total": 0,
            "status": f"Failed to fetch task with ID: {task_id}",
        }


@tasks_blueprint.route("/api/v2/tasks/<task_id>", methods=["GET"])
def get_logs_by_task_id(task_id):
    # Get all logs inside a task directory
    try:
        logs_dir = f"{LOG_DIRECTORY}/{task_id}"
        all_logs = [
            get_logs_status(logs_dir, f)
            for f in listdir(logs_dir)
            if isfile(join(logs_dir, f))
        ]
        return (jsonify({"logs": all_logs, "status": task_status(task_id)}), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return (jsonify({"error": e.__class__.__name__, "message": e.__str__()}), 400)


@tasks_blueprint.route("/api/v2/tasks/<task_id>/<log_file>", methods=["GET"])
@auth_required
def get_log_by_path(task_id, log_file):

    tail_timeout: int = request.args.get("ttimeout", 5, type=int)
    tail_count: int = request.args.get("tcount", 100, type=int)
    # Tail the last X lines from the log file and return it
    try:
        f_path = f"{LOG_DIRECTORY}/{task_id}/{log_file}"
        if not isfile(f_path):
            return (jsonify({"error": f"File {f_path} was not found"}), 404)
        current_app.logger.debug(
            "Tail timeout is: %s\nTail count is: %s", tail_timeout, tail_count
        )
        p1 = Popen(
            f"tail -n {tail_count} {f_path}",
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
            text=True,
        )
        content, error = p1.communicate(timeout=tail_timeout)
        _status: int = 300 if error else 200
        return (jsonify({"content": content, "error": error}), _status)
    except TimeoutExpired:
        current_app.logger.error("Failed to tail the file: %s", f_path, exc_info=1)
        return (
            jsonify(
                {
                    "error": "TimeoutExpired",
                    "message": f"Failed to tail the file -> {f_path} after {tail_timeout} seconds",
                }
            ),
            400,
        )
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return (jsonify({"error": e.__class__.__name__, "message": e.__str__()}), 400)


@tasks_blueprint.route("/api/v2/tasks/<task_id>/<log_file>/download", methods=["GET"])
@auth_required
def download_log_by_path(task_id, log_file):
    try:
        f_path = f"{LOG_DIRECTORY}/{task_id}/{log_file}"
        if not isfile(f_path):
            return (jsonify({"error": f"File {f_path} was not found"}), 404)
        return send_file(f_path, as_attachment=True)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return (jsonify({"error": e.__class__.__name__, "message": e.__str__()}), 400)
