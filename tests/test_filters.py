import unittest

import requests_mock

from troi.patch import Patch
from troi import Artist, ArtistCredit, Recording, Playlist
import troi.filters
from troi.musicbrainz.recording import RecordingListElement
from troi.listenbrainz.feedback import ListensFeedbackLookup


class DummyPatch:

    def __init__(self):
        self.local_storage = {}

    def set_patch_object(self, obj):
        pass


class TestArtistCreditFilterElement(unittest.TestCase):

    def test_artist_credit_filter_include(self):
        rlist = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist_credit=ArtistCredit(artist_credit_id=65)),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist_credit=ArtistCredit(artist_credit_id=197))
        ]
        alist = [197]

        e = troi.filters.ArtistCreditFilterElement(alist, include=True)
        flist = e.read([rlist])
        assert len(flist) == 1
        assert flist[0].artist_credit.artist_credit_id == 197
        assert flist[0].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"

        alist = [1]
        e = troi.filters.ArtistCreditFilterElement(alist, include=True)
        flist = e.read([rlist])
        assert len(flist) == 0

    def test_artist_credit_filter_exclude(self):
        rlist = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist_credit=ArtistCredit(artist_credit_id=65)),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist_credit=ArtistCredit(artist_credit_id=197))
        ]
        alist = [197]

        e = troi.filters.ArtistCreditFilterElement(alist)
        flist = e.read([rlist])
        assert len(flist) == 1
        assert flist[0].artist_credit.artist_credit_id == 65
        assert flist[0].mbid == "8756f690-18ca-488d-a456-680fdaf234bd"

        alist = [1]
        e = troi.filters.ArtistCreditFilterElement(alist)
        flist = e.read([rlist])
        assert len(flist) == 2


class TestArtistCreditLimiterElement(unittest.TestCase):

    def test_artist_credit_limiter_higher_ranked(self):
        rlist = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist_credit=ArtistCredit(artist_credit_id=65), ranking=1.0),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1', artist_credit=ArtistCredit(artist_credit_id=65), ranking=.5),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist_credit=ArtistCredit(artist_credit_id=197), ranking=.1)
        ]


        e = troi.filters.ArtistCreditLimiterElement(1)
        flist = e.read([rlist])
        assert len(flist) == 2
        assert flist[0].artist_credit.artist_credit_id == 65
        assert flist[0].mbid == "8756f690-18ca-488d-a456-680fdaf234bd"
        assert flist[1].artist_credit.artist_credit_id == 197
        assert flist[1].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"

        e = troi.filters.ArtistCreditLimiterElement(1, exclude_lower_ranked=False)
        flist = e.read([rlist])
        assert len(flist) == 2
        assert flist[0].artist_credit.artist_credit_id == 65
        assert flist[0].mbid == "139654ae-2c02-4e0f-aee0-c47da6e59ff1"
        assert flist[1].artist_credit.artist_credit_id == 197
        assert flist[1].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"

    def test_artist_credit_limiter_playlist(self):
        p = Playlist("test playlist")
        p.recordings = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist_credit=ArtistCredit(artist_credit_id=65), ranking=1.0),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1', artist_credit=ArtistCredit(artist_credit_id=65), ranking=.5),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist_credit=ArtistCredit(artist_credit_id=197), ranking=.1)
        ]

        p2 = Playlist("test playlist 2")
        p2.recordings = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist_credit=ArtistCredit(artist_credit_id=48), ranking=1.0),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist_credit=ArtistCredit(artist_credit_id=197), ranking=.1),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1', artist_credit=ArtistCredit(artist_credit_id=48), ranking=.5)
        ]

        e = troi.filters.ArtistCreditLimiterElement(1)
        plist = e.read([[p, p2]])
        assert len(plist) == 2
        assert len(plist[0].recordings) == 2
        assert plist[0].recordings[0].artist_credit.artist_credit_id == 65
        assert plist[0].recordings[0].mbid == "8756f690-18ca-488d-a456-680fdaf234bd"
        assert plist[0].recordings[1].artist_credit.artist_credit_id == 197
        assert plist[0].recordings[1].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"
        assert len(plist[1].recordings) == 2
        assert plist[1].recordings[0].artist_credit.artist_credit_id == 48
        assert plist[1].recordings[0].mbid == "8756f690-18ca-488d-a456-680fdaf234bd"
        assert plist[1].recordings[1].artist_credit.artist_credit_id == 197
        assert plist[1].recordings[1].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"


class TestDuplicateRecordingMBIDFilterElement(unittest.TestCase):

    def test_duplicate_recording_filter_element(self):
        rlist = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1'),
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e'),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1')
        ]
        e = troi.filters.DuplicateRecordingMBIDFilterElement()
        flist = e.read([rlist])
        assert len(flist) == 3

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'
        assert flist[2].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'


class TestConsecutiveRecordingFilterElement(unittest.TestCase):

    def test_consecutive_recording_filter_element(self):
        rlist = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1'),
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e'),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e'),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1')
        ]
        e = troi.filters.ConsecutiveRecordingFilterElement()
        flist = e.read([rlist])
        assert len(flist) == 5

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'
        assert flist[2].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[3].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'
        assert flist[4].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'


class TestYearRangeFilterElement(unittest.TestCase):

    def test_year_range_filter_element(self):
        rlist = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', year=1980),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', year=1990),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1', year=2000)
        ]
        e = troi.filters.YearRangeFilterElement(1985, 1995)
        flist = e.read([rlist])
        assert len(flist) == 1

        assert flist[0].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'

        e = troi.filters.YearRangeFilterElement(1985, 1995, inverse=True)
        flist = e.read([rlist])
        assert len(flist) == 2

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'

        e = troi.filters.YearRangeFilterElement(1985)
        flist = e.read([rlist])
        assert len(flist) == 2

        assert flist[0].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'

        e = troi.filters.YearRangeFilterElement(1985, inverse=True)
        flist = e.read([rlist])
        assert len(flist) == 1

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'


class TestHatedRecordingsFilterElement(unittest.TestCase):

    @requests_mock.Mocker()
    def test_hated_recordings_filter(self, mock_requests):
        mock_requests.get("https://api.listenbrainz.org/1/feedback/user/lucifer/get-feedback-for-recordings",
                          json={
                              "feedback": [{
                                  "created": None,
                                  "recording_mbid": "53969964-673a-4407-9396-3087be9245f6",
                                  "recording_msid": None,
                                  "score": 1,
                                  "track_metadata": None,
                                  "user_id": "lucifer"
                              }, {
                                  "created": None,
                                  "recording_mbid": "70c75409-4224-4bab-836a-eb5f3a9c31d3",
                                  "recording_msid": None,
                                  "score": -1,
                                  "track_metadata": None,
                                  "user_id": "lucifer"
                              }]
                          })

        recordings = RecordingListElement([
            Recording(mbid="53969964-673a-4407-9396-3087be9245f6"),
            Recording(mbid="70c75409-4224-4bab-836a-eb5f3a9c31d3"),
            Recording(mbid="8e7a9ff8-c31d-4ac0-a01d-20a7fcc28c8f")
        ])
        feedback_lookup = ListensFeedbackLookup(user_name="lucifer")
        feedback_lookup.set_sources(recordings)
        filter_element = troi.filters.HatedRecordingsFilterElement()
        filter_element.set_sources(feedback_lookup)

        received = filter_element.generate(quiet=True)
        expected = [
            Recording(mbid="53969964-673a-4407-9396-3087be9245f6", listenbrainz={"score": 1}),
            Recording(mbid="8e7a9ff8-c31d-4ac0-a01d-20a7fcc28c8f", listenbrainz={"score": 0})
        ]
        self.assertEqual(expected[0].mbid, received[0].mbid)
        self.assertEqual(expected[0].listenbrainz, received[0].listenbrainz)
        self.assertEqual(expected[1].mbid, received[1].mbid)
        self.assertEqual(expected[1].listenbrainz, received[1].listenbrainz)


class TestNeverListenedFilterElement(unittest.TestCase):

    def test_never_listened_element(self):
        rlist = [
            Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', listenbrainz={"latest_listened_at": 342134214}),
            Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', listenbrainz={"latest_listened_at": None}),
            Recording(mbid='c88b3490-35a0-460d-b3bc-bc50c8855d00'),
            Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1', listenbrainz={"latest_listened_at": 345345345})
        ]
        p = DummyPatch()
        e = troi.filters.NeverListenedFilterElement()
        e.set_patch_object(p)
        flist = e.read([rlist])
        assert len(flist) == 2

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'

        e = troi.filters.NeverListenedFilterElement(remove_unlistened=False)
        e.set_patch_object(p)
        flist = e.read([rlist])
        assert len(flist) == 2

        assert flist[0].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'
        assert flist[1].mbid == 'c88b3490-35a0-460d-b3bc-bc50c8855d00'
