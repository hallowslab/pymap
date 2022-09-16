import pytest
from core.pymap_core import ScriptGenerator

from tests import VALID_HOSTS, INVALID_HOSTS, RANDOM_VALID_CREDS


@pytest.mark.parametrize(
    "test_input",
    [
        # These should all return None
        (" "),
        ("\n\n\n\n\n\n"),
        ("n1x28ex31xe2"),
        ("random.email@gmail.com"),
        ("n1x28ex31xe2 random.email@gmail.com"),
        ("email@email.com \n n1x28ex31xe2"),
    ],
)
def test_discards_invalid_inputs(test_input):
    x = ScriptGenerator(VALID_HOSTS["cp"], VALID_HOSTS["cpp"], RANDOM_VALID_CREDS)
    assert (x.process_line(test_input)) is None


@pytest.mark.parametrize(
    "test_u1,test_p1, test_u2, test_p2",
    [
        ("test@mail.com", "Qwerty123", "test@mail.com", "Qwerty123",),
        ("test.test@mail.com", "Qwerty123", "test.test@mail.com", "Qwerty123"),
        ("test-test@mail.com", "Qwerty123", "test-test@mail.com", "Qwerty123"),
        (
            "test@email.com",
            "Espaços Funcionam Mas NSei se Deviam",
            "test@email.com",
            "Espaços Funcionam Mas NSei se Deviam",
        ),
        ("test@email.com", "Abc123!#$%&/()=", "test@email.com", "Abc123!#$%&/()="),
    ],
)
def test_returns_valid_inputs(test_u1, test_p1, test_u2, test_p2):
    x = ScriptGenerator(VALID_HOSTS["cp"], VALID_HOSTS["cpp"], RANDOM_VALID_CREDS)
    f_str = "imapsync --host1 {} --user1 {} --password1 '{}' --host2 {}  --user2 {} --password2 '{}' --log --logdir=....."
    # discard everything after --log we do not worry about that here
    out = x.process_line(" ".join([test_u1, test_p1, test_u2, test_p2])).split("--log")[
        0
    ]
    # do the same for the output to match
    assert (
        f_str.format(
            "cpanel01.dnscpanel.com",
            test_u1,
            test_p1,
            "premium01.dnscpanel.com",
            test_u2,
            test_p2,
        ).split("--log")[0]
        == out
    )


@pytest.mark.parametrize("test_input", RANDOM_VALID_CREDS)
def test_returns_parsed_line(test_input):
    x = ScriptGenerator(VALID_HOSTS["cp"], VALID_HOSTS["cpp"], RANDOM_VALID_CREDS)
    user1, passwd1, user2, passwd2 = test_input.split(" ")
    # final_str = x.FORMAT_STRING.format(VALID_HOSTS["cp"], user, passwd, VALID_HOSTS["cpp"], user, passwd)
    final_str = x.process_line(test_input)
    assert user1 in final_str
    assert passwd1 in final_str
    assert user2 in final_str
    assert passwd2 in final_str
    assert VALID_HOSTS["cp"] in final_str
    assert VALID_HOSTS["cpp"] in final_str


@pytest.mark.parametrize(
    "test_input,output",
    [
        # Should return as found
        ("", ""),
        ("invalid_host", "invalid_host"),
        ("127.0.0.1", "127.0.0.1"),
        ("cpanel1", "cpanel1"),
        # should return the appropriate hostname for the shortcut
        ("cpanel01", "cpanel01.dnscpanel.com"),
        ("premium04", "premium04.dnscpanel.com"),
        ("iberweb7a", "iberweb7a.ibername.com"),
        ("iberweb16", "iberweb16.ibername.com"),
        ("plesk08", "plesk08.host-services.com"),
        ("wp01", "wp01.host-services.com"),
        ("wp01-cpanel", "wp01.dnscpanel.com"),
        ("wp11cp", "wp11.dnscpanel.com"),
        ("wp11-cp", "wp11.dnscpanel.com"),
    ],
)
def test_returns_valid_hosts(test_input, output):
    x = ScriptGenerator(VALID_HOSTS["cp"], VALID_HOSTS["cpp"], RANDOM_VALID_CREDS)
    assert x.verify_host(test_input) == output
