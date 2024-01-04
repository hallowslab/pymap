import os
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
    # Test scenario 1: All should return None except the last line
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

