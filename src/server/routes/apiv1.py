from os import listdir, mkdir
from os.path import join, isdir, isfile
import subprocess


from flask import Blueprint, jsonify, request, url_for, current_app, send_file

from server.tasks import call_system
from server.utils import get_task_info, get_logs_status
from core.pymap_core import ScriptGenerator

apiv1_blueprint = Blueprint("apiV1", __name__)


# TODO: Move this to flask config
LOG_DIRECTORY = "/var/log/pymap"


# no need to register route V2 takes care of this
#@apiv1_blueprint.route("/api/v1/sync", methods=["POST"])
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


#@apiv1_blueprint.route("/api/v1/tasks", methods=["GET"])
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



