import re
import os
from typing import Generator, Iterable, List, Optional, Union

from core.tools import CustomLogger  # type: ignore


class ScriptGenerator:
    # STATIC CONSTANTS
    DOMAIN_IDENTIFIER = re.compile(r".*@(?P<domain>[\w]+.[\w]+)\s?.*")
    USER_IDENTIFIER = re.compile(r"^[\w.]+(?P<mail_provider>@[\w.]+)*")
    PASS_IDENTIFIER = re.compile(r".*[\s|,|.]+(?P<pword>.+)$")
    # Finding a delimiter for the password can be difficult since passwords
    # can be made up of almost any character
    WHOLE_STRING_ID = re.compile(
        r"^(?P<user1>[\w.-]+)(?P<domain1>@[\w.-]+)[ |,|\||\t]+(?P<pword1>.+)[ |,|\||\t]+(?P<user2>[\w.-]+?)(?P<domain2>@[\w.-]+)[ |,|\||\t]+(?P<pword2>.+)$"
    )
    IP_ADDR_RE = re.compile(r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}")

    def __init__(
        self,
        host1: str,
        host2: str,
        extra_args: str = "",
        **kwargs,
    ) -> None:
        self.logger = CustomLogger("PymapCore")
        self.config = kwargs.get("config", {})
        self.host1 = self.verify_host(host1)
        self.host2 = self.verify_host(host2)
        self.extra_args: Optional[str] = extra_args
        self.dest: str = kwargs.get("destination", "sync")
        self.line_count: int = kwargs.get("split", 30)
        self.file_count: int = 0
        self.domains: List[str] = []
        # STATIC VARIABLES
        self.LOGDIR = self.config.get("LOGDIR", "/var/log/pymap")
        self.FORMAT_STRING: str = (
            "imapsync --host1 {} --user1 {} --password1 '{}' --host2 {}  --user2 {} --password2 '{}' --log --logdir="
            + self.LOGDIR
            + " --logfile={} --addheader"
        )

    def match_domain(self, domain: str) -> Union[str, None]:
        has_match = re.match(self.DOMAIN_IDENTIFIER, domain)
        if has_match:
            return has_match.group("domain")
        return None

    # Verifies if the hostname is matched in the config file
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

    def process_file(self, fpath: str) -> None:
        """
        Reads a file line by line, creates the script for each line and then outputs to a file,
        creating a new file each time the counter is reached
        """
        if fpath != "" and os.path.isfile(fpath):
            try:
                lines = []
                with open(fpath, "r") as fh:
                    for line in self.line_generator(fh):
                        lines.append(line)
                        if len(lines) >= self.line_count:
                            self.write_output(lines)
                            lines.clear()
                    if len(lines) >= 1:
                        self.write_output(lines)
            except Exception as e:
                self.logger.critical(
                    "Unhandled exception: %s", e.__str__(), exc_info=True
                )
                raise
        else:
            raise ValueError(f"File path was not supplied: {fpath}")

    def process_strings(self, strings: List[str]) -> List[str]:
        """
        Processes data from a list with strings, uses self.line_generator to create the scripts,
        returns a list with all scripts
        """
        self.logger.dev("Supplied data: %s", strings)
        scripts = [x for x in self.line_generator(strings) if x is not None]
        return scripts

    # processes input -> yields str
    def line_generator(self, uinput: Iterable) -> Generator:
        """
        Just a generator wrapper for the process_line function,
        also appends <self.extra_args> if they exist

        Entrypoint for the data, other functions like process_strings and process_file should always call this
        """
        new_line = None
        for line in uinput:
            if line and len(line) > 1:
                # Check for domains
                domain = self.match_domain(line)
                self.domains = (
                    list(set(self.domains + [domain])) if domain else self.domains
                )
                # Process line
                new_line = self.process_line(line)
                if new_line:
                    # if extra arguments append at end
                    if self.extra_args:
                        new_line = f"{new_line} {self.extra_args}"
                    yield new_line

    def process_line(self, line: str) -> Union[str, None]:
        """
        Processes individual Lines returns None or a formatted string
        """
        self.logger.dev("Processing Line %s", line)
        has_match = re.match(self.WHOLE_STRING_ID, line)
        # FIXME: Regex has catastrophic backtracing, should not be used for now...
        # TODO: Maybe replace regex for the splitting logic
        if has_match:
            user1 = has_match.group("user1")
            user2 = has_match.group("user2")
            domain1 = has_match.group("domain1")
            domain2 = has_match.group("domain2")
            # Add domains to internal list
            self.logger.debug(f"Adding task: {user1}{domain1} -> {user2}{domain2}")
            username1: str = f"{user1}{domain1}" if user1 and domain1 else ""
            username2: str = f"{user2}{domain2}" if user2 and domain2 else ""
            if len(username1) > 5 and len(username2) > 5:
                return self.FORMAT_STRING.format(
                    self.host1,
                    username1,
                    has_match.group("pword1"),
                    self.host2,
                    username2,
                    has_match.group("pword2"),
                    f"{self.host1}__{self.host2}__{username1}--{username2}.log",
                )
            else:
                self.logger.warning("User missing domain or provider")
        else:
            self.logger.warning("Line did not match regex %s....", line[0:5])
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
                    self.logger.info("Line %s Matched trough fallback", line[0:5])
                    return self.FORMAT_STRING.format(
                        self.host1,
                        user1,
                        pword1,
                        self.host2,
                        user2,
                        pword2,
                        f"{self.host1}__{self.host2}__{user1}--{user2}.log",
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
