import unittest
from unittest.mock import patch

from troi import Recording
import troi.listenbrainz.recs

recording_ret = {
    "payload": {
        "count": 3,
        "entity": "recording",
        "last_updated": 1603372967,
        "mbids": [
            {
                "recording_mbid": "5b44c236-cbb0-4e54-a8b1-c344b76e1b8f",
                "score": 1.0
            },
            {
                "recording_mbid": "b6293447-05bf-4123-bfe5-099754348bbf",
                "score": .5
            },
            {
                "recording_mbid": "048e135c-204d-4d77-8e6a-203920768e4f",
                "score": .1
            }
        ],
        "offset": 0,
        "total_mbid_count": 1000,
        "type": "top",
        "user_name": "rob"
    }
}

class TestRecs(unittest.TestCase):

    @patch('liblistenbrainz.ListenBrainz.get_user_recommendation_recordings')
    def test_get_user_recommendation_recordings(self, recs_mock):

        recs_mock.return_value = recording_ret
        u = troi.listenbrainz.recs.UserRecordingRecommendationsElement("rob", artist_type="top", count=3, offset=0)
        entities = u.read()
        recs_mock.assert_called_with("rob", "top", count=3, offset=0)
        assert len(entities) == 3
        assert isinstance(entities[0], Recording)
        assert entities[0].mbid == '5b44c236-cbb0-4e54-a8b1-c344b76e1b8f'
        assert entities[0].ranking == 1.0
        assert entities[1].mbid == 'b6293447-05bf-4123-bfe5-099754348bbf'
        assert entities[1].ranking == .5
        assert entities[2].mbid == '048e135c-204d-4d77-8e6a-203920768e4f'
        assert entities[2].ranking == .1
