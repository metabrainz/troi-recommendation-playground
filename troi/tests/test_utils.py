import unittest

from troi.utils import discover_patches
from troi.patch import Patch


class TestPatches(unittest.TestCase):

    def test_discover_patches(self):
        patches = discover_patches()

        assert len(patches) == 7
        assert "daily-jams" in patches
        assert "area-random-recordings" in patches
        assert "weekly-flashback-jams" in patches
        assert "playlist-from-mbids" in patches
        assert "world-trip" in patches
        assert "recs-to-playlist" in patches
        assert "resave-playlist" in patches

        for p in patches:
            assert issubclass(patches[p], Patch)
