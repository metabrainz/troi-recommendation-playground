import unittest

from troi.utils import discover_patches
from troi.patch import Patch


class TestPatches(unittest.TestCase):

    def test_discover_patches(self):
        patches = discover_patches()

        assert len(patches) == 2
        assert "daily-jams" in patches
        assert "area-random-recordings" in patches

        assert issubclass(patches['daily-jams'], Patch)
        assert issubclass(patches['area-random-recordings'], Patch)
