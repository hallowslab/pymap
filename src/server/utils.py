import subprocess
from os import listdir
from os.path import isfile, join
import re

START_TIME_REGEX = re.compile(
    r"^Transfer started at (?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}).*"
)

LOGFILE_REGEX = re.compile(
    r"^(?P<source>[a-z0-9\-.]*)_(?P<dest>[a-z0-9\-.]*)_(?P<user1>[a-z0-9\-.@]*\.[a-z]{1,5})-(?P<user2>[a-z0-9\-.@]*)\.log$"
)

DATE_REGEX = re.compile(
    r".*(?P<time>[1-2][0-9]{3}-[0-1][0-9]-[0-3][0-9]\s[0-2][0-9]:[0-6][0-9]:[0-6][0-9]).*"
)


def check_status(code: str):
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
    codes = {
        "0": "✅",
        "1": "⚠ CatchAll",
        "6": "⚠ received Exit signal",
        "7": "⚠ Exit By File",
        "8": "⚠ Exit PID File Error",
        "10": "⛔Connection failure",
        "12": "⛔TLS Failure",
        "16": "⛔Authentication Failure",
        "21": "⚠ Subfolder 1 Does not exist",
        "111": "⚠ Exit With Errors",
        "112": "❌Reached max Errors",
        "113": "❌Reached max quota",
        "114": "📤Failed to append file or directory",
        "115": "📤Failed to fetch",
        "116": "📤Failed to create file/folder",
        "117": "⚠ Failed to select file/folder",
        "118": "❌Transfer exceeded",
        "119": "📥Failed to append, possible virus",
        "254": "⚠ Tests failed",
        "101": "📤Failed to connect on host1",
        "102": "📥Failed to connect on host2",
        "161": "📤Failed to authenticate user1",
        "162": "📥Failed to authenticate user2",
        "64": "❌Bad usage, possible invalid argument",
        "66": "❌Received no input",
        "69": "⚠ Service unavalilable?",
        "70": "❌ Internal Software error",
    }
    if code in codes.keys():
        return codes[code]
    return code


def get_logs_status(log_directory, log_path):
    grep_timeout = 5
    # FIXME: This might have some issues on directories with a large amount of files
    def sub_check_output(command: list, filename: str) -> str:
        try:
            return subprocess.check_output(
                [*command, filename], timeout=grep_timeout, text=True,
            )
        except subprocess.CalledProcessError:
            return f"Failed to run command: {command}"
        except subprocess.TimeoutExpired:
            return "Timeout expired"

    # Exit status

    # TODO: Maybe stop using so many regular expressions and just use grep awk and whatever.....
    status = sub_check_output(
        ["grep", "-E", "Exiting with return value *"], join(log_directory, log_path)
    ).split(" ")[4]
    status_message = check_status(status)
    start_time = sub_check_output(
        ["grep", "-E", "Transfer started at *"], join(log_directory, log_path)
    )
    start_time_match = re.match(DATE_REGEX, start_time)
    if start_time_match:
        start_time = start_time_match.group("time")

    # start_time = time.strptime(start_time, "%A  %B %Y-%m-%d")
    end_time = (
        sub_check_output(
            ["grep", "-E", "Transfer ended on *"], join(log_directory, log_path)
        )
        if status.strip() == "0"
        else "Check Status ->"
    )
    end_time_match = re.match(DATE_REGEX, end_time)
    if end_time_match:
        end_time = end_time_match.group("time")

    return {
        "logFile": log_path,
        "startTime": start_time,
        "endTime": end_time,
        "status": status_message,
    }


def get_task_info(task_path):
    file_list = [f for f in listdir(task_path) if isfile(join(task_path, f))]
    if len(file_list) == 0:
        return {"error": f"No files found in the task directory: {task_path}"}
    # select the first file in the list and remove the last 4 characters that should be ".log"
    for filename in file_list:
        # base f"{self.host1}_{self.host2}-{user}.log"
        match = re.match(LOGFILE_REGEX, filename)
        if match:
            return {
                "taskID": task_path.split("/")[-1],
                "source": match.group("source"),
                "dest": match.group("dest"),
                "domain": match.group("user1").split("@")[1],
                "count": len(file_list)
            }
        # Try to return as much data as possible
        elif not match:
            return {
                "taskID": task_path.split("/")[-1],
                "source": filename.split("_")[0],
                "dest": filename.split("_")[1].split("-")[0],
                "domain": filename.split("@")[1][:-4],
                "count": len(file_list)
            }
        return {"error": "Could not parse task status", "fileList": file_list}
