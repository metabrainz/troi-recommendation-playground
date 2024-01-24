import json
import unittest
import unittest.mock

import troi
import troi.listenbrainz.area_random_recordings

request_json = [
    {
        "area_id": "81",
        "end_year": "1985",
        "start_year": "1980"
    }
]

return_json = [
    {
        "artist_credit_id": 2926,
        "artist_credit_name": "Alphaville",
        "recording_mbid": "a10f5b03-5666-4c38-862d-7d2a2649e033",
        "recording_name": "In the Mood",
        "year": 1984
    },
    {
        "artist_credit_id": 1418,
        "artist_credit_name": "Tangerine Dream",
        "recording_mbid": "8f8cc91f-0bca-4351-90d4-ef334ac0a0cf",
        "recording_name": "Movements of a Visionary",
        "year": 1981
    }
]

class TestAreaRandomRecording(unittest.TestCase):

    @unittest.mock.patch('requests.post')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json)
        req.return_value = mock
        e = troi.listenbrainz.area_random_recordings.AreaRandomRecordingsElement(request_json[0]['area_id'],
                                                                                 request_json[0]['start_year'],
                                                                                 request_json[0]['end_year'])

        entities = e.read([[]])
        req.assert_called_with(e.SERVER_URL, json=request_json)

        assert len(entities) == 2
        assert entities[0].name == "In the Mood"
        assert entities[0].year == 1984
        assert entities[0].artist.name == "Alphaville"
        assert entities[0].artist.artist_credit_id == 2926
        assert entities[0].mbid == "a10f5b03-5666-4c38-862d-7d2a2649e033"

        assert entities[1].name == "Movements of a Visionary"
        assert entities[1].year == 1981
        assert entities[1].artist.name == "Tangerine Dream"
        assert entities[1].artist.artist_credit_id == 1418
        assert entities[1].mbid == "8f8cc91f-0bca-4351-90d4-ef334ac0a0cf"
