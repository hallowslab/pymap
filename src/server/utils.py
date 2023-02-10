import os
import subprocess
from os import listdir
from os.path import isfile, join
import re
from typing import Dict, List, Optional

from server.strings import (
    LOGFILE_REGEX,
    DATE_REGEX,
    SPAM_ERROR,
    DAVMAIL_PROPERTIES,
    IMAPSYNC_CODES,
)

from server.extensions import redis_store


def check_status(code: str) -> str:
    """
    0 OK
    1 CATCH_ALL
    6 EXIT_SIGNALLED
    7 EXIT_BY_FILE
    8 EXIT_PID_FILE_ERROR
    10 EXIT_CONNECTION_FAILURE
    12 EXIT_TLS_FAILURE
    16 EXIT_AUTHENTICATION_FAILURE
    21 EXIT_SUBFOLDER1_NO_EXISTS
    111 EXIT_WITH_ERRORS
    112 EXIT_WITH_ERRORS_MAX
    113 EXIT_OVERQUOTA
    114 EXIT_ERR_APPEND
    115 EXIT_ERR_FETCH
    116 EXIT_ERR_CREATE
    117 EXIT_ERR_SELECT
    118 EXIT_TRANSFER_EXCEEDED
    119 EXIT_ERR_APPEND_VIRUS
    254 EXIT_TESTS_FAILED
    101 EXIT_CONNECTION_FAILURE_HOST1
    102 EXIT_CONNECTION_FAILURE_HOST2
    161 EXIT_AUTHENTICATION_FAILURE_USER1
    162 EXIT_AUTHENTICATION_FAILURE_USER2
    64 BAD_USAGE
    66 NO_INPUT
    69 SERVICE_UNAVAILABLE
    70 INTERNAL_SOFTWARE_ERROR
    """

    if code in IMAPSYNC_CODES.keys():
        return IMAPSYNC_CODES[code]
    return code


def grep_errors(log_directory, log_path, timeout=5) -> str:
    try:
        content = subprocess.check_output(
            ["grep", "Err", join(log_directory, log_path)],
            timeout=timeout,
            text=True,
        )
        return content
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # return f"Failed to grep contents from file {join(log_directory, log_path)}"
        return ""


def check_failed_is_only_spam(content) -> bool:
    content = [x for x in content.split("\n") if len(x) > 1]
    for line in content:
        if re.match(SPAM_ERROR, line):
            continue
        else:
            return False
    return True


def sub_check_output(command: list, filename: str, timeout=5) -> str:
    f_path = os.path.abspath(filename)
    try:
        return subprocess.check_output(
            [*command, f_path],
            timeout=timeout,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Failed to run command: {command}:{e}"
    except subprocess.TimeoutExpired:
        return "Timeout expired"


def get_logs_status(log_directory, log_path, timeout=5) -> Dict[str, str]:
    # FIXME: This might have some issues on directories with a large amount of files
    # TODO: Maybe stop using so many regular expressions and just use grep awk and whatever.....
    status: str = sub_check_output(
        ["grep", "-E", "Exiting with return value *"], join(log_directory, log_path)
    ).split(" ")[4]
    status_message: str = check_status(status)
    start_time: str = sub_check_output(
        ["grep", "-E", "Transfer started at *"], join(log_directory, log_path)
    )
    start_time_match: Optional[re.Match] = re.match(DATE_REGEX, start_time)
    if start_time_match:
        start_time = start_time_match.group("time")
    else:
        start_time = "Failed to parse"

    # start_time = time.strptime(start_time, "%A  %B %Y-%m-%d")
    end_time: str = sub_check_output(
        ["grep", "-E", "Transfer ended on *"], join(log_directory, log_path)
    )
    end_time_match: Optional[re.Match] = re.match(DATE_REGEX, end_time)
    if end_time_match:
        end_time = end_time_match.group("time")
    else:
        end_time = "Check status ->"

    return {
        "logFile": log_path,
        "startTime": start_time,
        "endTime": end_time,
        "status": status_message,
    }


def get_task_info(task_path):
    file_list: List[str] = [f for f in listdir(task_path) if isfile(join(task_path, f))]
    if len(file_list) == 0:
        return {"error": f"No files found in the task directory: {task_path}"}
    # select the first file in the list and remove the last 4 characters that should be ".log"
    for filename in file_list:
        # base f"{self.host1}__{self.host2}--{user}.log"
        match = re.match(LOGFILE_REGEX, filename)
        if match:
            return {
                "taskID": task_path.split("/")[-1],
                "source": match.group("source"),
                "dest": match.group("dest"),
                "domain": match.group("user1").split("@")[1],
                "count": len(file_list),
            }
        # Try to return as much data as possible
        elif not match:
            return {
                "taskID": task_path.split("/")[-1],
                "source": filename.split("__")[0],
                "dest": filename.split("__")[1].split("--")[0],
                "domain": filename.split("@")[1][:-4],
                "count": len(file_list),
            }
        return {"error": "Could not parse task status", "fileList": file_list}


def create_new_davmail_properties(
    fname: str, uri: str, cport: int, iport: int, lport: int, pport: int, sport: int
) -> str:
    f_path = os.path.abspath(fname)
    new_props = (
        DAVMAIL_PROPERTIES.replace("davmail.url=", f"davmail.url={uri}")
        .replace("davmail.caldavPort=", f"davmail.caldavPort={cport}")
        .replace("davmail.imapPort=", f"davmail.imapPort={iport}")
        .replace("davmail.ldapPort=", f"davmail.ldapPort={lport}")
        .replace("davmail.popPort=", f"davmail.popPort={pport}")
        .replace("davmail.smtpPort=", f"davmail.smtpPort={sport}")
    )
    with open(f_path, "w") as fh:
        fh.write(new_props)
    return new_props

def log_redis(username:str, message:str, end: int = 99):
    redis_store.rpush(f"{username}_logs", message)
    redis_store.ltrim(f"{username}_logs", 0, end)