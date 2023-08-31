import pytest
from core.pymap_core import ScriptGenerator


@pytest.mark.parametrize(
    "h1_in, h2_in, h1_out, h2_out",
    [
        ("myserver21", "myserver2", "myserver21.example.com", "myserver2.example.com"),
        (
            "myserver2000",
            "myserver.example.com",
            "myserver2000",
            "myserver.example.com",
        ),
        ("mysql-0", "mysql9", "mysql-0.aws.com", "mysql9.aws.com"),
    ],
)
def test_core_matches_hosts(h1_in, h2_in, h1_out, h2_out):
    config = {
        "HOSTS": [["myserver[0-9]{1,2}", ".example.com"], ["mysql-?[0-9]", ".aws.com"]]
    }
    x = ScriptGenerator(h1_in, h2_in, config=config, creds="test_input")

    assert x.host1 == h1_out
    assert x.host2 == h2_out
