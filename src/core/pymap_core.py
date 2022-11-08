import logging
import re
from typing import Generator, Iterable, List, Union


LOGDIR = "/var/log/pymap"


class ScriptGenerator:
    DOMAIN_IDENTIFIER = re.compile(r"^([\w].[\w])*")
    USER_IDENTIFIER = re.compile(r"^[\w.]+(?P<mail_provider>@[\w.]+)*")
    PASS_IDENTIFIER = re.compile(r".*[\s|,|.]+(?P<pword>.+)$")
    # Finding a delimiter for the password can be difficult since passwords
    # can be made up of almost any character
    WHOLE_STRING_ID = re.compile(
        r"^(?P<user1>[\w.-]+)(?P<mail_provider1>@[\w.-]+)[ |,|\||\t]+(?P<pword1>.+)[ |,|\||\t]+(?P<user2>[\w.-]+?)(?P<mail_provider2>@[\w.-]+)[ |,|\||\t]+(?P<pword2>.+)$"
    )
    IP_ADDR_RE = re.compile(r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}")
    FORMAT_STRING = (
        "imapsync --host1 {} --user1 {} --password1 '{}' --host2 {}  --user2 {} --password2 '{}' --log --logdir="
        + LOGDIR
        + " --logfile={} --addheader"
    )

    def __init__(
        self, host1: str, host2: str, creds, extra_args: str = "", **kwargs
    ) -> None:
        self.logger = logging.getLogger("server")
        self.creds = creds
        self.lines: List[str] = []
        self.domain = kwargs.get("domain", "")
        self.dest = kwargs.get("destination", "sync")
        self.line_count = kwargs.get("split", 30)
        self.file_count = 0
        self.extra_args = extra_args if extra_args is not None else ""
        self.config = kwargs.get("config", {})
        self.host2 = self.verify_host(host2)
        self.host1 = self.verify_host(host1)

    # Verifies if the hostname is either a CPanel, Plesk or WEBLX instance
    # and returns the apropriate FQDN
    def verify_host(self, hostname: str) -> str:
        if self.config and len(self.config.get("HOSTS", [])) > 1:
            # Fetch hosts from config
            all_hosts = self.config.get("HOSTS")
            all_hosts = {k: v for k, v in [x for x in all_hosts]}
            for k in all_hosts:
                has_match = re.match(k, hostname)
                if has_match:
                    self.logger.debug("Matched hostname: %s", hostname)
                    if re.match(self.IP_ADDR_RE, all_hosts[k]):
                        self.logger.debug(
                            "Matched hostname: %s To address: %s",
                            hostname,
                            all_hosts[k],
                        )
                    return f"{hostname}{all_hosts[k]}"
        return hostname

    def process(self, mode: str = "file") -> Union[Exception, List]:
        self.logger.debug("Started with mode: %s", mode)
        if mode == "file":
            try:
                lines = []
                with open(self.creds, "r") as fh:
                    for line in self.process_input(fh):
                        lines.append(line)
                        if len(lines) >= self.line_count:
                            self.write_output(lines)
                            lines.clear()
                    if len(lines) >= 1:
                        self.write_output(lines)
                return lines
            except Exception as exc:
                self.logger.critical("Failed to process file: %s", exc)
                return exc
        elif mode == "api":
            # TODO: Strip out passwords before logging commands
            # self.logger.debug("Supplied data: %s", self.creds)
            scripts = [x for x in self.process_input(self.creds) if x is not None]
            return scripts
        return ValueError("Unkown mode: %s", mode)

    # processes input -> yields str
    def process_input(self, uinput: Iterable) -> Generator:
        new_line = None
        for line in uinput:
            if line and len(line) > 1:
                # Process line
                new_line = self.process_line(line)
                if new_line:
                    # if extra arguments append at end
                    if self.extra_args:
                        new_line = f"{new_line} {self.extra_args}"
                    # redirect stdout to /dev/null, we already have a log file
                    new_line = f"{new_line} > /dev/null"
                    yield new_line

    # Processes individual Lines returns None or a formatted string
    def process_line(self, line: str) -> Union[str, None]:
        # FIXME: Remove passwords before logging
        self.logger.debug("Processing Line %s....", line[0:5])
        has_match = re.match(self.WHOLE_STRING_ID, line)
        # FIXME: Regex has catastrophic backtracing, should not be used for now...
        # TODO: Maybe replace regex for the splitting logic
        if has_match:
            user1 = has_match.group("user1")
            user2 = has_match.group("user2")
            mail1 = has_match.group("mail_provider1")
            mail2 = has_match.group("mail_provider2")
            self.logger.debug(
                f"Adding users: {user1}{mail1} -> {user2}{mail2} to sync queue"
            )
            username1: str = (
                f"{user1}{mail1}"
                if mail1
                else f"{user1}{self.domain}"
                if self.domain
                else ""
            )
            username2: str = (
                f"{user2}{mail2}"
                if mail2
                else f"{user2}{self.domain}"
                if self.domain
                else ""
            )
            if len(username1) > 5 and len(username2) > 5:
                return self.FORMAT_STRING.format(
                    self.host1,
                    username1,
                    has_match.group("pword1"),
                    self.host2,
                    username2,
                    has_match.group("pword2"),
                    f"{self.host1}_{self.host2}_{username1}-{username2}.log",
                )
            else:
                self.logger.error("User missing domain or provider")
        else:
            self.logger.error("Line did not match regex %s....", line[0:5])
            try:
                new_line = re.sub("\t+", " ", line)
                new_line = re.sub("\s+", " ", new_line)
                new_line_split: List[str] = new_line.split(" ")
                if len(new_line_split) > 1:
                    user1 = new_line_split[0]
                    pword1 = new_line_split[1]
                    user2 = new_line_split[0]
                    pword2 = new_line_split[1]
                    if len(new_line_split) >= 4:
                        user2 = new_line_split[2]
                        pword2 = new_line_split[3]
                    self.logger.debug("Line %s Matched!!", line[0:5])
                    return self.FORMAT_STRING.format(
                        self.host1,
                        user1,
                        pword1,
                        self.host2,
                        user2,
                        pword2,
                        f"{self.host1}_{self.host2}_{user1}-{user2}.log",
                    )
            except Exception as e:
                self.logger.error("Line did not match split %s", line[0:5])
                self.logger.error("Error: %s", e)
                return None
        return None

    # Writes output to a file
    def write_output(self, lines: List[str]) -> None:
        dest = f"{self.dest}_{self.file_count}.sh"
        self.logger.debug("Writting %s lines to file %s", len(lines), dest)
        lines = [line + "\n" for line in lines]
        with open(dest, "w") as fh:
            fh.writelines(lines)
        self.file_count += 1
