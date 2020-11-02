import unittest
from unittest.mock import patch

from troi import Artist, Release, Recording
import troi.listenbrainz.stats

artist_ret = {
    'payload': {
        'artists': [
            {
                 'artist_mbids': [], 
                 'artist_msid': '7f65aec5-e7a7-4cfa-a6e5-e93e66a04990', 
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
                'artist_msid': 'c89e02cd-b309-43bb-81f7-d32493669ab8', 
                'artist_name': 'Saltillo', 
                'listen_count': 633, 
                'release_mbid': None, 
                'release_msid': '8408449c-e3bb-4d32-8391-0e4ebbacb041', 
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
                'artist_msid': '20b5aa89-8379-4c3f-8928-1ccf8c8aed15', 
                'artist_name': 'Woolfy', 
                'listen_count': 94, 
                'recording_mbid': None, 
                'recording_msid': '65435007-a8ea-48aa-9b23-5af1bd640905', 
                'release_mbid': None, 
                'release_msid': '1ae1ad70-03c9-4a37-a37b-9aca46504851', 
                'release_name': 'Stations', 
                'track_name': 'Tangiers'
            }
        ]
    }
}

class TestStats(unittest.TestCase):

    @patch('pylistenbrainz.ListenBrainz.get_user_artists')
    def test_user_artist_stats(self, stats_mock):

        stats_mock.return_value = artist_ret
        u = troi.listenbrainz.stats.UserArtistsElement("rob", 1, 1, "week")
        entities = u.read()
        stats_mock.assert_called_with("rob", 1, 1, "week")
        assert len(entities) == 1
        assert isinstance(entities[0], Artist)
        assert entities[0].mbids == None
        assert entities[0].msid == '7f65aec5-e7a7-4cfa-a6e5-e93e66a04990'
        assert entities[0].name == 'Pretty Lights'

    @patch('pylistenbrainz.ListenBrainz.get_user_releases')
    def test_user_release_stats(self, stats_mock):

        stats_mock.return_value = release_ret
        u = troi.listenbrainz.stats.UserReleasesElement("rob", 1, 1, "all_time")
        entities = u.read()
        stats_mock.assert_called_with("rob", 1, 1, "all_time")
        assert len(entities) == 1
        assert isinstance(entities[0], Release)
        assert entities[0].artist.msid == 'c89e02cd-b309-43bb-81f7-d32493669ab8'
        assert entities[0].artist.name == 'Saltillo'
        assert entities[0].msid == '8408449c-e3bb-4d32-8391-0e4ebbacb041'
        assert entities[0].name == 'Ganglion'

    @patch('pylistenbrainz.ListenBrainz.get_user_recordings')
    def test_user_recording_stats(self, stats_mock):

        stats_mock.return_value = recording_ret
        u = troi.listenbrainz.stats.UserRecordingElement("rob", 1, 1, "all_time")
        entities = u.read()
        stats_mock.assert_called_with("rob", 1, 1, "all_time")
        assert len(entities) == 1
        assert isinstance(entities[0], Recording)
        assert entities[0].artist.msid == '20b5aa89-8379-4c3f-8928-1ccf8c8aed15'
        assert entities[0].artist.name == 'Woolfy'
        assert entities[0].release.msid == '1ae1ad70-03c9-4a37-a37b-9aca46504851'
        assert entities[0].release.name == 'Stations'
        assert entities[0].name == 'Tangiers'
        assert entities[0].msid == '65435007-a8ea-48aa-9b23-5af1bd640905'
