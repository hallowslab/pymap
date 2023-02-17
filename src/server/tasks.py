import sys
import shlex
import subprocess
import time
from typing import List

import logging
import celery.signals

from server import create_celery_app

celery_app = create_celery_app(sys.argv[1:])
logger = logging.getLogger(__name__)

# TODO: This is not working, find a way to do proper logging....
@celery.signals.setup_logging.connect
def on_celery_setup_logging(**kwargs):
    if not logger.handlers:
        handler = logging.FileHandler("celery_tasks.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s >>> %(levelname)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False


@celery_app.task(bind=True)
def call_system(self, cmd_list: List[str]) -> dict:
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
        print("Task %s Scheduling %s" % (call_system.request.id, index))
        n_cmd = subprocess.Popen(
            shlex.split(cmd),
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        running_procs[str(index)] = n_cmd
        while len(running_procs) >= max_procs:
            print("%s Waiting for Queue" % call_system.request.id)
            running_procs = check_running(running_procs)
            time.sleep(4)
        # FIXME: Pending is not correct AFAIK
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
    print("Finished Task: %s" % call_system.request.id)
    return {"status": "Executed all commands", "return_codes": finished_procs}
