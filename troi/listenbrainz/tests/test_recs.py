import os
import sys
import unittest
from unittest.mock import patch

import ujson
from troi import Artist, Release, Recording
import troi.listenbrainz.recs

recording_ret = {
    "payload": {
        "count": 3,
        "last_updated": 1595499525,
        "top_artist": {
            "recording_mbid": [
                "00440193-f84c-4e3d-b23c-a96d21c050e6",
                "0222ff68-4590-49b7-b063-c625e0f735ed",
                "03037817-867c-445d-8fbf-56e754b4a537"
            ]
        },
        "total_recording_mbids_count": 200,
        "user_name": "rob"
    }
}

class TestRecs(unittest.TestCase):

    @patch('pylistenbrainz.ListenBrainz.get_user_recommendation_recordings')
    def test_get_user_recommendation_recordings(self, recs_mock):

        recs_mock.return_value = recording_ret
        u = troi.listenbrainz.recs.UserRecordingRecommendationsElement("rob", artist_type="top", count=3, offset=0)
        entities = u.read()
        recs_mock.assert_called_with("rob", "top", 3, 0)
        assert len(entities) == 3
        assert isinstance(entities[0], Recording)
        assert entities[0].mbid == '00440193-f84c-4e3d-b23c-a96d21c050e6'
        assert entities[1].mbid == '0222ff68-4590-49b7-b063-c625e0f735ed'
        assert entities[2].mbid == '03037817-867c-445d-8fbf-56e754b4a537'
