import unittest

from troi import Artist, Release, Recording, Playlist


class TestEntities(unittest.TestCase):

    def test_artist(self):

        a = Artist()
        assert a.mbids is None
        assert a.name is None
        assert a.artist_credit_id is None
        with self.assertRaises(TypeError):
            a = Artist(mbids="not a list")

        a = Artist("Portishead", ["8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"], ranking=1.0)
        assert a.name == "Portishead"
        assert a.mbids == ["8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"]
        assert a.ranking == 1.0

        a = Artist("Portishead", ["afe3f1d4-b6d5-4726-89ad-926e3420b9e3", "97b01626-65fc-4c32-b30c-c4d7eab1b339"])
        assert len(a.mbids)
        assert a.mbids[0] == "97b01626-65fc-4c32-b30c-c4d7eab1b339"
        assert a.mbids[1] == "afe3f1d4-b6d5-4726-89ad-926e3420b9e3"

        a = Artist("Portishead", artist_credit_id=65)
        assert a.artist_credit_id == 65

        a = Artist(listenbrainz={ 1 : 2}, musicbrainz={ 3 : 4}, acousticbrainz={ 5 : 6})
        assert a.lb[1] == 2
        assert a.mb[3] == 4
        assert a.ab[5] == 6
        assert a.name is None
        assert a.mbid is None

    def test_release(self):

        r = Release()
        assert r.mbid is None
        assert r.name is None

        r = Release("Dummy", "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3", ranking=.5)
        assert r.name == "Dummy"
        assert r.mbid == "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"
        assert r.ranking == .5

        r = Release(listenbrainz={ 1 : 2}, musicbrainz={ 3 : 4}, acousticbrainz={ 5 : 6})
        assert r.lb[1] == 2
        assert r.mb[3] == 4
        assert r.ab[5] == 6
        assert r.name is None
        assert r.mbid is None

    def test_recording(self):

        r = Recording()
        assert r.mbid is None
        assert r.msid is None
        assert r.name is None

        r = Recording("Strangers", "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3", 
                      "97b01626-65fc-4c32-b30c-c4d7eab1b339", ranking=.1, year=1995)
        assert r.name == "Strangers"
        assert r.mbid == "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"
        assert r.msid == "97b01626-65fc-4c32-b30c-c4d7eab1b339"
        assert r.ranking == .1
        assert r.year == 1995

        r = Recording(listenbrainz={ 1 : 2}, musicbrainz={ 3 : 4}, acousticbrainz={ 5 : 6})
        assert r.lb[1] == 2
        assert r.mb[3] == 4
        assert r.ab[5] == 6
        assert r.name is None
        assert r.mbid is None
        assert r.msid is None


    def test_playlist(self):

        r = Playlist()
        assert r.mbid is None
        assert r.name is None
        assert r.filename is None
        assert r.recordings == None

        p = Playlist("cooking playlist", "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3", "mk_noms.jspf")
        assert p.name == "cooking playlist"
        assert p.mbid == "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"
        assert p.filename == "mk_noms.jspf"
        assert p.recordings == None

        r = Recording("Strangers", "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3", "97b01626-65fc-4c32-b30c-c4d7eab1b339")
        p = Playlist("eating playlist", "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3", "omnomnom.jspf", [r])
        assert p.name == "eating playlist"
        assert p.mbid == "8fe3f1d4-b6d5-4726-89ad-926e3420b9e3"
        assert p.filename == "omnomnom.jspf"
        assert p.recordings == [r]
