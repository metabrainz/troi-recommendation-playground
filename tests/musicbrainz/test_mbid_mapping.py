import json
import unittest
import unittest.mock

import troi
import troi.musicbrainz.mbid_mapping

return_data = [
    {
        "artist_credit_arg": "morcheeba",
        "artist_credit_id": 963,
        "artist_credit_name": "Morcheeba",
        "index": 0,
        "recording_arg": "trigger hippie",
        "recording_mbid": "97e69767-5d34-4c97-b36a-f3b2b1ef9dae",
        "recording_name": "Trigger Hippie",
        "release_mbid": "9db51cd6-38f6-3b42-8ad5-559963d68f35",
        "release_name": "Who Can You Trust?",
        "artist_mbids": ["067102ea-9519-4622-9077-57ca4164cfbb"]
    }
]


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    e = troi.musicbrainz.mbid_mapping.MBIDMappingLookupElement()
    if args[0] == e.SERVER_URL:
        return MockResponse(return_data, 200)

    return MockResponse(None, 404)


class TestMBIDMapping(unittest.TestCase):

    @unittest.mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_read(self, req):

        e = troi.musicbrainz.mbid_mapping.MBIDMappingLookupElement()

        r = [ troi.Recording("trigger hippie", artist_credit=troi.ArtistCredit(name="morcheeba")) ]
        entities = e.read([r])
        req.assert_called_with(e.SERVER_URL, json=[{'artist_credit_name': 'morcheeba', 'recording_name': 'trigger hippie'}])

        assert len(entities) == 1
        assert entities[0].artist_credit.artist_credit_id == 963
        assert entities[0].artist_credit.name == "Morcheeba"
        assert entities[0].artist_credit.artists[0].mbid == "067102ea-9519-4622-9077-57ca4164cfbb"
        assert entities[0].release.mbid == "9db51cd6-38f6-3b42-8ad5-559963d68f35"
        assert entities[0].release.name == "Who Can You Trust?"
        assert entities[0].mbid == "97e69767-5d34-4c97-b36a-f3b2b1ef9dae"
        assert entities[0].name == "Trigger Hippie"

    @unittest.mock.patch('requests.post')
    def test_read_remove_unmatched(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = "{}"
        req.return_value = mock
        e = troi.musicbrainz.mbid_mapping.MBIDMappingLookupElement(True)

        r = [ troi.Recording("track not found", artist_credit=troi.ArtistCredit(name="artist not found")) ]
        entities = e.read([r])
        assert len(entities) == 0
