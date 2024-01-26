import subprocess
import re
from os import listdir
from os.path import isfile, join, abspath

from typing import Optional, Dict, List

from migrator.utilites.strings import (
    LOGFILE_REGEX,
    DATE_REGEX,
    SPAM_ERROR,
    DAVMAIL_PROPERTIES,
    IMAPSYNC_CODES,
)


def check_status(code: str) -> str:
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
    f_path = abspath(filename)
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
    print("STATUS", status)
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
        "log_file": log_path,
        "start_time": start_time,
        "end_time": end_time,
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
