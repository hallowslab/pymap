import os
import sys
import math
from random import choice
from string import ascii_letters

ALL_CHARS = [c for c in ascii_letters]

# Converts Bytes into KBs/MBs/GBs
# https://stackoverflow.com/a/14822210
def convert_bytes(size_bytes:int, output:str="MB"):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

# Returns number of bytes in a string
# https://stackoverflow.com/a/30686735
def utf8len(s):
    return len(s.encode('utf-8'))

def write_file(line):
    with open("large_file.txt", "a") as out_file:
        out_file.write(line)


def generate_random_text(line_count, line_lenght):
    for _ in range(line_count+1):
        new_str = "".join([choice(ALL_CHARS) for _ in range(line_lenght+1)])
        write_file(new_str)
        print("Wrote %s" % convert_bytes(utf8len(new_str)))

def run_checks():
    if os.path.isfile("large_file.txt"):
        sys.exit(1)


if __name__ == "__main__":
    run_checks()
    generate_random_text(100, 9000000)