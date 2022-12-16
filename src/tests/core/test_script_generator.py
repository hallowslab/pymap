import pytest
from core.pymap_core import ScriptGenerator

from tests import RANDOM_VALID_CREDS_2, RANDOM_VALID_CREDS


@pytest.mark.parametrize(
    "test_input",
    [
        # These should all return None
        (""),
        ("n1x28ex31xe2"),
        ("random.email@gmail.com"),
        # Except this
        ("This gets parsed by the second method, unfortunately returns bad content"),
    ],
)
def test_discards_invalid_inputs(test_input):
    x = ScriptGenerator("127.0.0.1", "127.0.0.1", test_input, domain="test.com")
    if "This gets parsed" in test_input:
        # As explained above the fallback logic tries to find the user and password
        # Refer to core.
        # +0
        # .0213pymap_core.process_line
        final_str = x.process_line(test_input)
        assert "--user1 This" in final_str
        assert "--password1 'gets'" in final_str
    else:
        # All others should fail and return None
        assert x.process_line(test_input) is None


# USER1 PASSWORD1 USER2 PASSWORD2""
@pytest.mark.parametrize("test_input", RANDOM_VALID_CREDS_2)
def test_returns_parsed_line_2_users(test_input):
    x = ScriptGenerator("127.0.0.1", "127.0.0.1", test_input, domain="test.com")
    user1, passwd1, user2, passwd2 = test_input.split(" ")
    final_str = x.process_line(test_input)
    assert f"--user1 {user1}" in final_str
    assert f"--password1 '{passwd1}'" in final_str
    assert f"user2 {user2}" in final_str
    assert f"--password2 '{passwd2}'" in final_str
    assert final_str.count(user1) == 2
    assert final_str.count(user2) == 2
    assert "--host1 127.0.0.1" in final_str
    assert "--host2 127.0.0.1" in final_str


# Same but for lines that match "USER PASSWORD"
@pytest.mark.parametrize("test_input", RANDOM_VALID_CREDS)
def test_returns_parsed_line_1_user(test_input):
    x = ScriptGenerator("127.0.0.1", "127.0.0.2", test_input, domain="test.com")
    user1, passwd1 = test_input.split(" ")
    final_str = x.process_line(test_input)
    assert f"--user1 {user1}" in final_str
    assert f"--password1 '{passwd1}'" in final_str
    assert f"--user2 {user1}" in final_str
    assert f"--password2 '{passwd1}'" in final_str
    # Usernames appear in log file
    assert final_str.count(user1) == 4
    assert final_str.count(passwd1) == 2
    assert "127.0.0.1" in final_str
    assert "127.0.0.2" in final_str


# TODO: test functionality to use alias from config files
