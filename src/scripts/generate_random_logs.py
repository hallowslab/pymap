import os
import random
import string


RANDOM_TASK_IDS = [
    "da19d48d-289e-4283-919e-d1cd9d29fef2",
    "c146c211-b659-4e59-9696-c045790cc0e4",
    "281defdb-2a8f-4210-bd86-817b87d14930",
    "aad2b030-54fe-4f7e-9674-8533a0484043",
]

RANDOM_TASK_LOGS = [
    "cpanel01.dnscpanel.com_iberweb12.ibername.com-test@mail.com.log",
    "127.0.0.1_mail.dominio.pt-test@mail.com.log",
    "127.0.0.1_91.91.91.91-test.test@mail.com.log",
    "localhost_localhost-test2@mail.com.log",
    "cpanel01_cpanel02-test+archive@mail.com.log",
]

RANDOM_LENGHTS = [
    25,
    39,
    53,
    84,
]

RANDOM_WRITES = [10, 20, 30, 40]


def run():
    for id in RANDOM_TASK_IDS:
        new_dir = os.path.join("/var/log/pymap/", id)
        if not os.path.isdir(new_dir):
            os.mkdir(new_dir)
        for i in range(0, 10):
            letters = [*string.ascii_lowercase, *string.ascii_uppercase]
            new_file = os.path.join(new_dir, random.choice(RANDOM_TASK_LOGS))
            with open(new_file, "w") as fh:
                for _ in range(random.choice(RANDOM_WRITES)):
                    rand_string = (
                        "".join(
                            random.choice(letters)
                            for i in range(random.choice(RANDOM_LENGHTS))
                        )
                        + "\n"
                    )
                    fh.write(rand_string)
    exit(0)


if __name__ == "__main__":
    run()
