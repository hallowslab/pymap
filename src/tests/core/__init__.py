import os
import tempfile

from tests import RANDOM_VALID_CREDS, RANDOM_VALID_CREDS_2, RANDOM_INVALID


class ScriptGeneratorTest:
    """Base test class for all ScriptGenerator tests"""

    def setup_method(self):
        self.invalid = tempfile.NamedTemporaryFile(mode="w", delete=False)
        self.invalid.write("\n".join(RANDOM_INVALID))
        self.invalid.close()
        self.r1 = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.r1.write('\n'.join(RANDOM_VALID_CREDS))
        self.r1.close()
        self.r2 = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.r2.write('\n'.join(RANDOM_VALID_CREDS_2))
        self.r2.close()

    def teardown_method(self):
        os.unlink(self.invalid.name)
        os.unlink(self.r1.name)
        os.unlink(self.r2.name)
