# myapp/tasks.py
import shlex
import subprocess
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from celery import shared_task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django_celery_results.models import TaskResult

from migrator.models import CeleryTask
from pymap import celery_app

logger = get_task_logger("CeleryTask")

FProc = Dict[str, (str | int)]
RProc = Dict[str, Any]


@shared_task(bind=True)
def call_system(self, cmd_list: List[str]) -> Dict[str, (str | FProc)]:
    root_directory: str = settings.PYMAP_LOGDIR
    total_cmds: int = len(cmd_list)
    max_procs: int = 5
    finished_procs: Dict[str, (str | int)] = {}
    running_procs: RProc = {}
    task_id = self.request.id
    log_directory = Path(root_directory, task_id)

    for i, cmd in enumerate(cmd_list):
        cmd_list[i] = cmd.replace(
            f"--logdir={root_directory}",
            f"--logdir={log_directory}",
        )

    # Just to ensure if the task is the one creating the path
    if not log_directory.exists():
        log_directory.mkdir()
    # Moved the check to the task itself to verify for cases of overwritting contents,
    # this will be slow if the directory has a lot of contents
    if len(sorted(log_directory.rglob("*.*"))) > 0:
        logger.warning(
            "Directory: %s seems to already exist and isn't completely empty, we might be overwritting files",
            log_directory,
        )

    def check_running(procs: RProc) -> RProc:
        for key in list(procs):
            proc = procs[key]
            if isinstance(proc, subprocess.Popen):
                status = proc.poll()
                if status is None:
                    continue
                else:
                    logger.info("Marked for removal: %s", key)
                    finished_procs[key] = status
                    procs.pop(key, None)
        return procs

    for index, cmd in enumerate(cmd_list):
        logger.info("Task %s Scheduling %s", task_id, index)
        # Some complex passwords or our regex/custom logic might fail to create a viable
        # "command" string, in this case let shlex fail to avoid shell escapes
        try:
            split_cmd = shlex.split(cmd)
        except ValueError:
            logger.critical("Failed to parse and split the string received")
            logger.debug(
                "Received the following command string: %s", cmd, exc_info=True
            )
            # Continue to the next iteration of the loop
            continue
        n_cmd = subprocess.Popen(
            shlex.split(cmd),
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        running_procs[str(index)] = n_cmd
        while len(running_procs) >= max_procs:
            logger.info("%s Waiting for Queue", task_id)
            running_procs = check_running(running_procs)
            time.sleep(4)

        self.update_state(
            state="PROGRESS",
            meta={
                "processing": len(running_procs),
                "pending": len(cmd_list),
                "total": total_cmds,
                "return_codes": finished_procs,
                "status": "Processing...",
            },
        )

    while running_procs:
        running_procs = check_running(running_procs)
        nrp = len(running_procs)
        self.update_state(
            state="PROGRESS",
            meta={
                "processing": nrp,
                "pending": nrp,
                "total": total_cmds,
                "return_codes": finished_procs,
                "status": "Processing...",
            },
        )
        time.sleep(4)

    logger.info("Finished Task: %s , calculating run time...", task_id)
    ctask = CeleryTask.objects.get(task_id=task_id)

    # Calculate run time in seconds
    # TODO: Investigate celery's builtin runtime calculation
    # https://stackoverflow.com/questions/33860242/extract-runtime-and-time-of-completion-from-celery-task

    start_time = ctask.start_time
    end_time = timezone.now()
    run_time_seconds = int((end_time - start_time).total_seconds())

    logger.debug("START TIME: %s", ctask.start_time)
    logger.debug("RUN TIME: %s", run_time_seconds)

    # Update the run_time field in the database
    ctask.run_time = run_time_seconds
    # Make sure to mark the task as finished
    ctask.finished = True
    ctask.save()

    return {"status": "Executed all commands", "return_codes": finished_procs}


# I'm not sure how the django admin scheduler passes the arguments, assuming as string
@shared_task
def purge_results(
    days: int = int("1"), hours: int = int("0"), minutes: int = int("0")
) -> None:
    try:
        days = int(days)
        hours = int(hours)
        minutes = int(minutes)
    except ValueError:
        logger.error(
            "Invalid values passed to purge results: Days %s, Hours %s, Minutes %s",
            days,
            hours,
            minutes,
        )
        days = 1
        hours = 0
        minutes = 0
    # Calculate the cutoff date
    td = timedelta(days=days, hours=hours, minutes=minutes)
    cutoff_date = datetime.now() - td
    logger.info("Starting purge of results older than: %s", td)

    # Filter the queryset to get tasks older than the cutoff date
    tasks = CeleryTask.objects.filter(start_time__lt=cutoff_date)
    logger.info("We will try to purge %s results", len(tasks))

    for task in tasks:
        try:
            result = AsyncResult(task.task_id, app=celery_app)
            result.forget()
        except TimeoutError:
            logger.error("Failed to clear results for Task ID:%s", task.task_id)
        try:
            result = TaskResult.objects.filter(task_id=task.task_id)
            if result.exists():
                result.delete()
            else:
                logger.info(
                    "We don't seem to have any results associated with: %s",
                    task.task_id,
                )
        except ImproperlyConfigured:
            # If TaskResult model is not available, log or handle the situation
            logger.warning("Task results backend is not configured to use django-db.")
        except Exception as e:
            logger.critical("Unhandled exception %s", e, exc_info=True)


# Some tasks where not being set as finished, can also be run periodically
# for tasks that may have crashed
@shared_task
def validate_finished() -> None:
    logger.info("Checking for non running unfinished tasks")
    unfinished = CeleryTask.objects.filter(finished=False)
    for task in unfinished:
        # Check status to ensure task is not running:
        # https://docs.celeryq.dev/en/latest/reference/celery.result.html#celery.result.AsyncResult.status
        result = AsyncResult(task.task_id, app=celery_app)
        if result.status in ["FAILURE", "SUCCESS"]:
            logger.info("Setting task %s as finished", task.task_id)
            task.finished = True
            task.save()
