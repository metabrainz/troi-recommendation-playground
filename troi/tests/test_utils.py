import unittest

from troi.utils import discover_patches
from troi.patch import Patch


class TestPatches(unittest.TestCase):

    def test_discover_patches(self):
        patches = discover_patches()

        assert len(patches) == 4
        assert "daily-jams" in patches
        assert "area-random-recordings" in patches
        assert "ab-similar-recordings" in patches
        assert "weekly-flashback-jams" in patches

        assert issubclass(patches['daily-jams'], Patch)
        assert issubclass(patches['area-random-recordings'], Patch)
