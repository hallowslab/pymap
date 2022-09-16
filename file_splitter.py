import argparse
import logging
import math
import os
from os.path import abspath
from posixpath import split
import re
import sys

logger = logging.getLogger()


# Converts Bytes into KBs/MBs/GBs
# https://stackoverflow.com/a/14822210
def convert_bytes(size_bytes:int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

# Returns number of bytes in a string
# https://stackoverflow.com/a/30686735
def utf8len(s:str) -> int:
    return len(s.encode('utf-8'))

# Try to parse log level, default to 20/INFO
def set_logging(**kwargs):
    # On dry run DEBUG is always enabled
    log_level = kwargs.get("log_level")
    dry_run = kwargs.get("dry_run")
    if dry_run:
        logging.basicConfig(
            format="%(asctime)s - %(name)s >>> %(levelname)s: %(message)s",
            level=logging.DEBUG,
            datefmt="%d/%m/%Y %I:%M:%S %p",
        )
    else:
        numeric_level = getattr(logging, log_level.upper(), 20)
        logging.basicConfig(
            format="%(asctime)s - %(name)s >>> %(levelname)s: %(message)s",
            level=numeric_level,
            datefmt="%d/%m/%Y %I:%M:%S %p",
        )
    logging.info("Logging instantiated with log level: %s", logging.getLevelName(logging.getLogger().level))


def setup_argparse():
    parser = argparse.ArgumentParser(
        description="Processes an input file, splits into multiple smaller files",
        prog="FileSplitter",
        epilog="The end",
    )
    parser.add_argument("input", type=str, help="File to split")
    parser.add_argument("output", type=str, help="Destination directory", default="")
    parser.add_argument(
        "-s",
        "--size",
        type=int,
        default=250,
        help="Specifies the size in megabytes to split the file",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default="INFO",
        help="Defines log level (INFO, WARNING, ERROR, DEBUG)",
    )
    parser.add_argument(
        "-dry",
        "--dry-run",
        action="store_true",
        default=False,
        help="Does not write to file only outputs debug",
    )
    args = parser.parse_args()
    return args


def run_checks(**kwargs):
    in_file = kwargs.get("input", None)
    out_file = kwargs.get("output", None)
    split_size = kwargs.get("size", None)
    if not os.path.isfile(in_file):
        logger.critical("Couldn't find a file at: %s", in_file)
        sys.exit(1)
    elif os.path.isfile(out_file):
        logger.critical("There is already a file at: %s", out_file)
        sys.exit(1)
    elif split_size == None or split_size <= 0:
        logger.critical("Invalid split size: %s", split_size)
        sys.exit(1)

def write_file(content, out_file, iteration):
    def process_name(value:str) -> str:
        has_match = re.match(r"^(?P<filename>[A-Za-z0-9._]*)?\.(?P<extension>[a-z]{1,15})$", value)
        if has_match:
            return "%s%s.%s" % (has_match.group("filename"), iteration, has_match.group("extension"))
        else:
            logger.error("Failed to process file name with regex, trying other methods....")
            split_dot = str(out_file).split(".")
            file_name = "".join(text for text in split_dot if text != split_dot[-1])
            ext = split_dot[-1]
            return "%s%s.%s" % (file_name, iteration, ext)
    file_name = process_name(out_file)
    with open(file_name, "w") as fh:
        fh.write(content)

def file_splitter(in_file, out_file, split_size):
    logger.info("Starting splitter")
    logger.debug("Input: %s", in_file)
    logger.debug("Output: %s", out_file)
    logger.debug("Split size: %s", split_size)
    current_line = ""
    iteration = 0
    with open(in_file, "r") as fh:
        for line in fh:
            print(len(line))
            current_line = "".join([current_line, line]) if current_line == "" else "\n".join([current_line, line])
            current_length = utf8len(current_line)
            logger.debug("Current legth - split size: %s - %s", current_length, split_size)
            if current_length >= split_size:
                logger.debug("Writting %s to file", convert_bytes(current_length))
                write_file(current_line, out_file, iteration)
                iteration = iteration + 1
                current_line = ""
    if current_line != "":
        write_file(current_line, out_file, iteration)

        


if __name__ == "__main__":
    args = setup_argparse()
    set_logging(**vars(args))
    run_checks(**vars(args))
    in_file = getattr(args, "input", None)
    out_file = getattr(args, "output", None)
    split_size = getattr(args, "size", None)
    file_splitter(in_file, out_file, split_size)

