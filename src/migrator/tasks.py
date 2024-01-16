# myapp/tasks.py
import shlex
import subprocess
import time
from typing import List

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

logger = get_task_logger(__name__)


@shared_task(bind=True)
def call_system(self, cmd_list: List[str]) -> dict:
    total_cmds = len(cmd_list)
    max_procs = 4
    finished_procs = {}
    running_procs = {}

    cmd_list = [
        cmd.replace(
            "--logdir=/var/log/pymap",
            f"--logdir=/var/log/pymap/{self.request.id}",
        )
        for cmd in cmd_list
    ]

    def check_running(procs):
        for key in list(procs):
            proc = procs[key]
            status = proc.poll()
            if status is None:
                continue
            else:
                logger.info("Marked for removal: %s", key)
                finished_procs[key] = status
                procs.pop(key, None)
        return procs

    for index, cmd in enumerate(cmd_list):
        logger.info("Task %s Scheduling %s", self.request.id, index)
        n_cmd = subprocess.Popen(
            shlex.split(cmd),
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        running_procs[str(index)] = n_cmd
        while len(running_procs) >= max_procs:
            logger.info("%s Waiting for Queue", self.request.id)
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

    logger.info("Finished Task: %s", self.request.id)
    return {"status": "Executed all commands", "return_codes": finished_procs}
