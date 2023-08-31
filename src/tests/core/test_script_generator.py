import os
import pytest
from core.pymap_core import ScriptGenerator

from tests.core import ScriptGeneratorTest


class TestScriptGenerator(ScriptGeneratorTest):
    def test_discards_invalid_inputs(self):
        x = ScriptGenerator(
            "127.0.0.1", "127.0.0.1", file_path=self.invalid.name, out_file="/tmp/sync"
        )
        # All others should fail and return None
        x.process_file()
        with open("/tmp/sync_0.sh", "r") as fh:
            fh.readlines()

        # assert len(contents) == 0

    def test_returns_parsed_line_1_user(self):
        # Test scenario 1: USER PASSWORD
        x = ScriptGenerator(
            "127.0.0.1", "127.0.0.2", file_path=self.r1.name, out_file="/tmp/sync"
        )
        contents = []
        output = []
        with open(self.r1.name, "r") as fh:
            contents = [x.strip() for x in fh.readlines()]
        x.process_file()

        assert os.path.isfile("/tmp/sync_0.sh")

        with open("/tmp/sync_0.sh", "r") as fh:
            output = fh.read()
        for item in contents:
            u1, p1 = item.split(" ")
            assert u1 in output
            assert p1 in output
        assert "--host1 127.0.0.1" in output
        assert "--host2 127.0.0.2" in output

    def test_returns_parsed_line_2_users(self):
        # Test scenario 1: USER1 PASSWORD1 USER2 PASSWORD2
        x = ScriptGenerator(
            "127.0.0.1", "127.0.0.1", file_path=self.r2.name, out_file="/tmp/sync"
        )
        contents = []
        output = []
        with open(self.r2.name, "r") as fh:
            contents = [x.strip() for x in fh.readlines()]
        x.process_file()
        assert os.path.isfile("/tmp/sync_0.sh")

        with open("/tmp/sync_0.sh", "r") as fh:
            output = fh.read()
        for item in contents:
            u1, p1, u2, p2 = item.split(" ")
            assert u1 in output
            assert p1 in output
            assert u2 in output
            assert p2 in output
        assert "--host1 127.0.0.1" in output
        assert "--host2 127.0.0.1" in output

    def test_process_file_no_path(self):
        with pytest.raises(ValueError, match="File path was not supplied: None"):
            x = ScriptGenerator(
                "127.0.0.1",
                "127.0.0.1",
                creds="",
                file_path=None,
            )
            x.process_file()

        with pytest.raises(ValueError, match="File path was not supplied: "):
            x = ScriptGenerator(
                "127.0.0.1",
                "127.0.0.1",
                creds="",
                file_path="",
            )
            x.process_file()


# @pytest.mark.parametrize("file_path", RANDOM_VALID_CREDS_2)
# def test_process_file_with_valid_file_path(file_path):

#     x = ScriptGenerator(
#         "127.0.0.1", "127.0.0.1", file_path=file_path
#     )
#     x.process_file()

#     # Verify that the output was written to the expected file
#     assert os.path.exists("sync_0.sh")


# TODO: test functionality to use alias from config files
