import os
import unittest

from troi import Artist, Release, Recording


class TestOperations(unittest.TestCase):

    def test_artist(self):

        with self.assertRaises(TypeError):
            a = Artist(mbids="not a list")

        a = Artist("Portishead", ["8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"], "97b01626-65fc-4c32-b30c-c4d7eab1b339")
        assert a.name == "Portishead"
        assert a.mbids == ["8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"]
        assert a.msid == "97b01626-65fc-4c32-b30c-c4d7eab1b339"

        a = Artist("Portishead", ["afe3f1d4-b6d5-4726-89ad-926e3420b9e3", "97b01626-65fc-4c32-b30c-c4d7eab1b339"])
        assert len(a.mbids)
        assert a.mbids[0] == "97b01626-65fc-4c32-b30c-c4d7eab1b339"
        assert a.mbids[1] == "afe3f1d4-b6d5-4726-89ad-926e3420b9e3"

        a = Artist(listenbrainz={ 1 : 2}, musicbrainz={ 3 : 4}, acousticbrainz={ 5 : 6})
        assert a.lb[1] == 2
        assert a.mb[3] == 4
        assert a.ab[5] == 6
        assert a.name == None
        assert a.mbid == None
        assert a.msid == None
