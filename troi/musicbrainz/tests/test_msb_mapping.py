import os
import unittest
import unittest.mock

import troi
import troi.musicbrainz.msb_mapping

return_json = """[

    {
        "artist_arg": "morcheeba",
        "index": 0,
        "mb_artist_credit_id": 963,
        "mb_artist_name": "Morcheeba",
        "mb_recording_mbid": "97e69767-5d34-4c97-b36a-f3b2b1ef9dae",
        "mb_recording_name": "Trigger Hippie",
        "mb_release_mbid": "9db51cd6-38f6-3b42-8ad5-559963d68f35",
        "mb_release_name": "Who Can You Trust?",
        "recording_arg": "triggerhippie"
    }

]"""

class TestMSBMapping(unittest.TestCase):

    @unittest.mock.patch('requests.get')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = return_json
        req.return_value = mock
        e = troi.musicbrainz.msb_mapping.MSBMappingLookupElement()

        r = [ troi.Recording("trigger hippie", artist=troi.Artist("morcheeba")) ]
        entities = e.read([r])
        req.assert_called_with(e.SERVER_URL, params={'[msb_artist_credit_name]': 'morcheeba', '[msb_recording_name]': 'trigger hippie'})

        assert len(entities) == 1
        assert entities[0].artist.artist_credit_id == 963
        assert entities[0].artist.name == "Morcheeba"
        assert entities[0].release.mbid == "9db51cd6-38f6-3b42-8ad5-559963d68f35"
        assert entities[0].release.name == "Who Can You Trust?"
        assert entities[0].mbid == "97e69767-5d34-4c97-b36a-f3b2b1ef9dae"
        assert entities[0].name == "Trigger Hippie"


    @unittest.mock.patch('requests.get')
    def test_read_remove_unmatched(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = "{}"
        req.return_value = mock
        e = troi.musicbrainz.msb_mapping.MSBMappingLookupElement(True)

        r = [ troi.Recording("track not found", artist=troi.Artist("artist not found")) ]
        entities = e.read([r])
        assert len(entities) == 0
