import logging
import re
import os
from typing import Generator, Iterable, List, Optional, Union

class ScriptGenerator:
    DOMAIN_IDENTIFIER = re.compile(r".*@(?P<domain>[\w]+.[\w]+)\s?.*")
    USER_IDENTIFIER = re.compile(r"^[\w.]+(?P<mail_provider>@[\w.]+)*")
    PASS_IDENTIFIER = re.compile(r".*[\s|,|.]+(?P<pword>.+)$")
    # Finding a delimiter for the password can be difficult since passwords
    # can be made up of almost any character
    WHOLE_STRING_ID = re.compile(
        r"^(?P<user1>[\w.-]+)(?P<domain1>@[\w.-]+)[ |,|\||\t]+(?P<pword1>.+)[ |,|\||\t]+(?P<user2>[\w.-]+?)(?P<domain2>@[\w.-]+)[ |,|\||\t]+(?P<pword2>.+)$"
    )
    IP_ADDR_RE = re.compile(r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}")
    # TODO: Find a way to load this from the supplied config
    LOGDIR = "/var/log/pymap"
    FORMAT_STRING = (
        "imapsync --host1 {} --user1 {} --password1 '{}' --host2 {}  --user2 {} --password2 '{}' --log --logdir="
        + LOGDIR
        + " --logfile={} --addheader"
    )

    def __init__(
        self,
        host1: str,
        host2: str,
        creds: Union[List[str], str],
        extra_args: str = "",
        **kwargs,
    ) -> None:
        self.logger = logging.getLogger("PymapCore")
        self.creds = creds
        self.lines: List[str] = []
        self.dest: str = kwargs.get("destination", "sync")
        self.line_count: int = kwargs.get("split", 30)
        self.file_count: int = 0
        self.extra_args: Optional[str] = extra_args
        self.config = kwargs.get("config", {})
        self.host2 = self.verify_host(host2)
        self.host1 = self.verify_host(host1)
        self.domains: List[str] = []
        # self.domain = self.find_first_domain(kwargs.get("domain", ""))

    def update_domains(self, domains: List[str]) -> None:
        """
        Checks if any of the <domains> in the list is present in self.domains, adds it in case it's missing
        """
        self.domains = list(set(self.domains + domains))

    def find_domains(self, from_file:bool=False)->List[str]:
        """
        Parses domains from the input, in case it's a file needs to open it to read,
        Returns a list with strings of domains
        """
        domains = []
        def match_domain(domain:str)-> Union[str,None]:
            has_match = re.match(self.DOMAIN_IDENTIFIER, domain)
            if has_match:
                return has_match.group("domain")
            return None

        if from_file:
            with open(self.creds, "r", encoding="utf-8") as fh:
                for line in fh:
                    parts = line.split(" ")
                    for pvt in parts:
                        matched = match_domain(pvt)
                        if matched:
                            self.logger.debug("Matched domain <%s> from file: %s", matched, self.creds)
                            domains = list(set(domains + [matched]))
                        else:
                            self.logger.dev("Analised part | %s .... | of line | %s | didn't match anything", pvt, line)
        return domains
        

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

    # Processes input based on type, a list with strings or a file
    def process_input(self) -> None:
        if isinstance(self.creds, List):
            self.find_domains()
            self.process_strings(self.creds)
        elif isinstance(self.creds, str):
            self.find_domains(from_file=True)
            self.process_file(self.creds)
        else:
            self.logger.critical(f"Unknown Value: {self.creds}")
            raise ValueError(f"Unknown Value: {self.creds}")

    def process_file(self, fpath: str) -> None:
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
        # TODO: Strip out passwords before logging commands
        self.logger.dev("Supplied data: %s", self.creds)
        scripts = [x for x in self.line_generator(strings) if x is not None]
        return scripts

    # processes input -> yields str
    def line_generator(self, uinput: Iterable) -> Generator:
        new_line = None
        for line in uinput:
            if line and len(line) > 1:
                # Process line
                new_line = self.process_line(line)
                if new_line:
                    # if extra arguments append at end
                    if self.extra_args:
                        new_line = f"{new_line} {self.extra_args}"
                    yield new_line

    # Processes individual Lines returns None or a formatted string
    def process_line(self, line: str) -> Union[str, None]:
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
            self.update_domains([domain1,domain2])
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
