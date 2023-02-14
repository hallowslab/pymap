import os
import unittest.mock
import pytest
from server.utils import (
    check_status,
    grep_errors,
    check_failed_is_only_spam,
    sub_check_output,
    create_new_davmail_properties,
    log_redis,
)



CONTENTS_1 = """
++++ Listing 1 errors encountered during the sync ( avoid this listing with --noerrorsdump ).
Err 1/10: Host1 failure: Error login on [] with user [] auth [LOGIN]: 2 NO LOGIN Failed - Invalid username or password.
Err 2/10 Host2 Folder INBOX.spam: Could not select: 21 NO Mailbox doesn't exist: INBOX.spam (0.001 + 0.000 secs).
Err 3/10 Host2 Folder INBOX.spam: Could not select: 21 NO Mailbox doesn't exist: INBOX.spam (0.001 + 0.000 secs).
"""
CONTENTS_2 = """
Detected 0 errors

Check if a new imapsync release is available by adding --releasecheck
Homepage: https://imapsync.lamiral.info/
Exiting with return value 0 (EX_OK: successful termination) 0/50 nb_errors/max_errors
"""


@pytest.fixture
def create_logs():
    with open("local.log", "w") as fh:
        fh.write(CONTENTS_1)
    with open("local2.log", "w") as fh:
        fh.write(CONTENTS_2)


@pytest.mark.parametrize(
    "input,expected",
    [
        ("0", "✅"),
        ("1", "⚠ CatchAll"),
        ("6", "⚠ received Exit signal"),
        ("70", "❌ Internal Software error"),
        ("1000780", "1000780"),
    ],
)
def test_status_codes(input, expected):
    assert check_status(input) == expected


def test_grep_errors():
    x = grep_errors(".", "local.log")
    x = check_failed_is_only_spam(x)
    assert x is False
    y = grep_errors(".", "local2.log")
    assert y == ""
    y = check_failed_is_only_spam(y)
    assert y is True


@pytest.mark.parametrize(
    "input,expected",
    [
        (["grep", "Detected"], "Detected 0 errors"),
        (["grep", "Homepage"], "Homepage: https://imapsync.lamiral.info/"),
    ],
)
def test_sub_check_output(input: list, expected, create_logs):
    x = sub_check_output(input, "local2.log")
    assert x.strip() == expected


@pytest.mark.parametrize(
    "fname,uri,cport,iport,lport,pport,sport",
    [
        (
            "davmail1.properties",
            "https://example.com",
            "1143",
            "1144",
            "1145",
            "1146",
            "1147",
        ),
        (
            "davmail2.properties",
            "https://test.com",
            "11143",
            "11144",
            "11145",
            "11146",
            "11147",
        ),
    ],
)
def test_creates_dav_props(fname, uri, cport, iport, lport, pport, sport):
    x = create_new_davmail_properties(fname, uri, cport, iport, lport, pport, sport)
    assert os.path.isfile(os.path.abspath(fname))
    assert f"davmail.url={uri}" in x
    assert f"davmail.caldavPort={cport}" in x
    assert f"davmail.imapPort={iport}" in x
    assert f"davmail.ldapPort={lport}" in x
    assert f"davmail.popPort={pport}" in x
    assert f"davmail.smtpPort={sport}" in x


def test_log_redis():
    with unittest.mock.patch("redis.StrictRedis.rpush") as mock_rpush:
        log_redis("username", "message")
        mock_rpush.assert_called_once_with("username_logs", "message")

    with unittest.mock.patch("redis.StrictRedis.ltrim") as mock_ltrim:
        log_redis("username", "message")
        mock_ltrim.assert_called_once_with("username_logs", 0, 99)
