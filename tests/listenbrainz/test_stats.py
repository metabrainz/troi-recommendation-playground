import unittest
from unittest.mock import patch

from troi import Artist, ArtistCredit, Release, Recording
import troi.listenbrainz.stats

artist_ret = {
    'payload': {
        'artists': [
            {
                 'artist_mbids': [], 
                 'artist_name': 'Pretty Lights',
                 'listen_count': 1641
            }
         ]
     }
}

release_ret = {
    'payload': {
        'count': 25, 
        'from_ts': 1009843200, 
        'last_updated': 1593870248, 
        'offset': 0, 
        'range': 'all_time', 
        'releases': [
            {
                'artist_mbids': [], 
                'artist_name': 'Saltillo',
                'listen_count': 633, 
                'release_mbid': None, 
                'release_name': 'Ganglion'
            }
        ]
    }
}

recording_ret = {
    'payload': {
        'count': 25, 
        'from_ts': 1009843200, 
        'last_updated': 1593872937, 
        'offset': 0, 
        'range': 'all_time', 
        'recordings': [
            {
                'artist_mbids': [], 
                'artist_name': 'Woolfy',
                'listen_count': 94, 
                'recording_mbid': None, 
                'release_mbid': None, 
                'release_name': 'Stations',
                'track_name': 'Tangiers'
            }
        ]
    }
}

class TestStats(unittest.TestCase):

    @patch('liblistenbrainz.ListenBrainz.get_user_artists')
    def test_user_artist_stats(self, stats_mock):

        stats_mock.return_value = artist_ret
        u = troi.listenbrainz.stats.UserArtistsElement("rob", 1, 1, "week")
        entities = u.read()
        stats_mock.assert_called_with("rob", 1, 1, "week")
        assert len(entities) == 1
        assert isinstance(entities[0], ArtistCredit)
        assert entities[0].name == 'Pretty Lights'
        assert len(entities[0].artists) == 0

    @patch('liblistenbrainz.ListenBrainz.get_user_releases')
    def test_user_release_stats(self, stats_mock):

        stats_mock.return_value = release_ret
        u = troi.listenbrainz.stats.UserReleasesElement("rob", 1, 1, "all_time")
        entities = u.read()
        stats_mock.assert_called_with("rob", 1, 1, "all_time")
        assert len(entities) == 1
        assert isinstance(entities[0], Release)
        assert entities[0].artist_credit.name == 'Saltillo'
        assert entities[0].name == 'Ganglion'

    @patch('liblistenbrainz.ListenBrainz.get_user_recordings')
    def test_user_recording_stats(self, stats_mock):

        stats_mock.return_value = recording_ret
        u = troi.listenbrainz.stats.UserRecordingElement("rob", 1, 1, "all_time")
        entities = u.read()
        stats_mock.assert_called_with("rob", 1, 1, "all_time")
        assert len(entities) == 1
        assert isinstance(entities[0], Recording)
        assert entities[0].artist_credit.name == 'Woolfy'
        assert entities[0].release.name == 'Stations'
        assert entities[0].name == 'Tangiers'
