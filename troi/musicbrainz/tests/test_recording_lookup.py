import json
import unittest
import unittest.mock

import troi
import troi.musicbrainz.recording_lookup

request_json = [
                    { "[recording_mbid]": "a96bf3b6-651d-49f4-9a89-eee27cecc18e" }, 
                    { "[recording_mbid]": "ec5b8aa9-7483-4791-a185-1f599a0cdc35" }
               ]

return_json = [
    {
        "[artist_credit_mbids]": [
            "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11"
        ],
        "artist_credit_id": 65,
        "artist_credit_name": "Portishead",
        "comment": "",
        "length": 253000,
        "recording_mbid": "a96bf3b6-651d-49f4-9a89-eee27cecc18e",
        "recording_name": "Sour Times",
        "release_name": "Dummy",
        "release_mbid": "cf2a6e34-b4b7-4164-a464-dbb3dbf09c28",
        "original_recording_mbid": "a96bf3b6-651d-49f4-9a89-eee27cecc18e",
        "canonical_recording_mbid": "a96bf3b6-651d-49f4-9a89-eee27cecc18e",
    },
    {
        "[artist_credit_mbids]": [
            "31810c40-932a-4f2d-8cfd-17849844e2a6"
        ],
        "artist_credit_id": 11,
        "artist_credit_name": "Squirrel Nut Zippers",
        "comment": "",
        "length": 275333,
        "recording_mbid": "cfa47c9b-f12f-4f9c-a6da-22a9355d6125",
        "recording_name": "Blue Angel",
        "release_name": "Hot",
        "release_mbid": "70fc4df9-1a86-4357-aac7-0694d4248aed",
        "original_recording_mbid": "ec5b8aa9-7483-4791-a185-1f599a0cdc35",
        "canonical_recording_mbid": "cfa47c9b-f12f-4f9c-a6da-22a9355d6125",
    }
]


class TestRecordingLookup(unittest.TestCase):

    @unittest.mock.patch('requests.post')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json)
        req.return_value = mock
        e = troi.musicbrainz.recording_lookup.RecordingLookupElement()

        inputs = [ troi.Recording(mbid="a96bf3b6-651d-49f4-9a89-eee27cecc18e"), 
                   troi.Recording(mbid="ec5b8aa9-7483-4791-a185-1f599a0cdc35") ]
        entities = e.read([inputs])
        req.assert_called_with(e.SERVER_URL % len(inputs), json=request_json)

        assert len(entities) == 2
        assert entities[0].name == "Sour Times"
        assert entities[0].duration == 253000
        assert entities[0].artist.name == "Portishead"
        assert entities[0].artist.artist_credit_id == 65
        assert entities[0].mbid == "a96bf3b6-651d-49f4-9a89-eee27cecc18e"
        assert entities[0].release.mbid == "cf2a6e34-b4b7-4164-a464-dbb3dbf09c28"
        assert entities[0].release.name == "Dummy"

        assert entities[1].name == "Blue Angel"
        assert entities[1].duration == 275333
        assert entities[1].artist.name == "Squirrel Nut Zippers"
        assert entities[1].artist.artist_credit_id == 11
        assert entities[1].mbid == "cfa47c9b-f12f-4f9c-a6da-22a9355d6125"
        assert entities[1].release.mbid == "70fc4df9-1a86-4357-aac7-0694d4248aed"
        assert entities[1].release.name == "Hot"
