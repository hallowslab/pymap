import os
import subprocess
import time
from typing import List

import logging
from celery import Celery
from celery.utils.log import get_task_logger
import celery.signals


# configure celery
celery_app = Celery(__name__)
celery_app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery_app.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)

# TODO: This is not working, find a way to do proper logging....
@celery.signals.setup_logging.connect
def on_celery_setup_logging(**kwargs):
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.FileHandler('celery_tasks.log')
        formatter = logging.Formatter("%(asctime)s - %(name)s >>> %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False


@celery_app.task(bind=True)
def call_system(self, cmd_list: List[str]) -> bool:
    # task_logger.debug("Command list %s", cmd_list)
    total_cmds = len(cmd_list)
    max_procs = 4
    finished_procs = {}
    running_procs = {}
    # Replace the log directory in each command adding the current task id as the parent directory
    cmd_list = [
        cmd.replace(
            "--logdir=/var/log/pymap",
            f"--logdir=/var/log/pymap/{call_system.request.id}",
        )
        for cmd in cmd_list
    ]

    def check_running(procs):
        for key in procs.keys():
            print("POLLING: %s" % key)
            # Poll the process, if running returns None, else returns exit code
            proc = procs[key]
            status = proc.poll()
            if status is None:
                continue
            else:
                # procs.pop(index)
                print("Marked for removal: %s" % key)
                finished_procs[key] = status
                procs = {
                    k: v for k, v in procs.items() if k not in finished_procs.keys()
                }
        return procs

    for index, cmd in enumerate(cmd_list):
        print("Scheduling %s" % index)
        n_cmd = subprocess.Popen(cmd, stdin=None, stdout=None, stderr=None, shell=True)
        running_procs[str(index)] = n_cmd
        while len(running_procs) >= max_procs:
            print("%s Waiting on Queue" % call_system.request.id)
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
    while len(running_procs) > 0:
        print("Waiting on last tasks")
        running_procs = check_running(running_procs)
        nrp = len(running_procs)
        print("Running procs %s" % nrp)
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
    print("Finished Task: %s" % call_system.request.id)
    return {"status": "Executed all commands", "return_codes": finished_procs}
