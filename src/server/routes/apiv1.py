from os import listdir, mkdir
from os.path import join, isdir, isfile
import subprocess

from subprocess import TimeoutExpired

from flask import Blueprint, jsonify, request, url_for, current_app, send_file

from server.tasks import call_system
from server.utils import get_task_info, get_logs_status
from server.models import CeleryTask, User
from server import db
from core.pymap_core import ScriptGenerator

apiv1_blueprint = Blueprint("api", __name__)


# TODO: Move this to flask config
LOG_DIRECTORY = "/var/log/pymap"


@apiv1_blueprint.route("/api/v1/sync", methods=["POST"])
def parse_creds():
    content = request.json
    # TODO: Strip out passwords before logging data
    # current_app.logger.debug("Parsing the following json data:\n %s", content)
    source = content.get("source")
    dest = content.get("destination")
    creds = content.get("input")
    extra_args = content.get("extra_args", None)
    extra_args = None if extra_args == "" else extra_args
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
    ctask = CeleryTask(source, dest, f"/var/log/pymap/{task.id}", task.id)
    db.session.add(ctask)
    db.session.commit()
    if not isdir(f"/var/log/pymap/{task.id}"):
        mkdir(f"/var/log/pymap/{task.id}")
    current_app.logger.info("Starting background task with ID: %s", task.id)
    return (
        jsonify(
            {"location": url_for("api.task_status", task_id=task.id), "taskID": task.id}
        ),
        202,
    )


@apiv1_blueprint.route("/api/v1/task-status/<task_id>", methods=["GET"])
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


@apiv1_blueprint.route("/api/v1/tasks", methods=["GET"])
def get_tasks():
    # Get all tasks
    try:
        task_list = [
            f
            for f in listdir(LOG_DIRECTORY)
            if isdir(join(LOG_DIRECTORY, f)) and f != "history" and f != ".history"
        ]
        all_tasks = [get_task_info(join(LOG_DIRECTORY, f)) for f in task_list]
        # TODO: Handle errors, or just return the array with tasks: or error:
        return (jsonify({"tasks": all_tasks}), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return jsonify({"error": e.__class__.__name__, "message": e.__str__()}, 400)


@apiv1_blueprint.route("/api/v1/tasks/<task_id>", methods=["GET"])
def get_logs_by_task_id(task_id):
    # Get all logs inside a task directory
    try:
        logs_dir = f"{LOG_DIRECTORY}/{task_id}"
        # TODO: Maybe we should send all the info trough here: start time, status, etc......
        # look for Transfer started on ............ Transfer ended on ............
        # Transfer started on: Thursday  5 May 2022-05-05 09:27:19 +0100 WEST
        all_logs = [
            get_logs_status(logs_dir, f)
            for f in listdir(logs_dir)
            if isfile(join(logs_dir, f))
        ]
        return (jsonify({"logs": all_logs, "status": task_status(task_id)}), 200)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return (jsonify({"error": e.__class__.__name__, "message": e.__str__()}), 400)


@apiv1_blueprint.route("/api/v1/tasks/<task_id>/<log_file>", methods=["GET"])
def get_log_by_path(task_id, log_file):

    tail_timeout = request.args.get("ttimeout", 5, type=int)
    tail_count = request.args.get("tcount", 100, type=int)
    # Tail the last X lines from the log file and return it
    try:
        f_path = f"{LOG_DIRECTORY}/{task_id}/{log_file}"
        if not isfile(f_path):
            return (jsonify({"error": f"File {f_path} was not found"}), 404)
        current_app.logger.debug(
            "Tail timeout is: %s\nTail count is: %s", tail_timeout, tail_count
        )
        p1 = subprocess.Popen(
            f"tail -n {tail_count} {f_path}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )
        content, error = p1.communicate(timeout=tail_timeout)
        _status = 300 if error else 200
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


@apiv1_blueprint.route("/api/v1/tasks/<task_id>/<log_file>/download", methods=["GET"])
def download_log_by_path(task_id, log_file):
    try:
        f_path = f"{LOG_DIRECTORY}/{task_id}/{log_file}"
        if not isfile(f_path):
            return (jsonify({"error": f"File {f_path} was not found"}), 404)
        return send_file(f_path, as_attachment=True)
    except Exception as e:
        current_app.logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
        return (jsonify({"error": e.__class__.__name__, "message": e.__str__()}), 400)
