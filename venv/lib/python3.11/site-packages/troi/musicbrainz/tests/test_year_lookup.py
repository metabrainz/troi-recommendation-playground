import json
import unittest
import unittest.mock

import troi
import troi.musicbrainz.year_lookup

return_json = [
    {
        "artist_credit_name": "morcheeba",
        "recording_name": "trigger hippie",
        "year": 1997
    }
]

# intentionally empty
return_json_keep_unmatched = [ ]

class TestYearLookup(unittest.TestCase):

    @unittest.mock.patch('requests.post')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json)
        req.return_value = mock
        e = troi.musicbrainz.year_lookup.YearLookupElement()

        r = [ troi.Recording("trigger hippie", artist=troi.Artist("morcheeba")) ]
        entities = e.read([r])
        req.assert_called_with(e.SERVER_URL, json=[{ '[recording_name]': 'trigger hippie', '[artist_credit_name]': 'morcheeba' }])

        assert len(entities) == 1
        assert entities[0].artist.name == "morcheeba"
        assert entities[0].name == "trigger hippie"
        assert entities[0].year == 1997


    @unittest.mock.patch('requests.post')
    def test_read_remove_unmatched(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = "{}"
        req.return_value = mock
        e = troi.musicbrainz.year_lookup.YearLookupElement()

        r = [ troi.Recording("track not found", artist=troi.Artist("artist not found")) ]
        entities = e.read([r])
        assert len(entities) == 0

    @unittest.mock.patch('requests.post')
    def test_read_keep_unmatched(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json_keep_unmatched)
        req.return_value = mock
        e = troi.musicbrainz.year_lookup.YearLookupElement(skip_not_found=False)

        r = [ troi.Recording("trigger hippie", artist=troi.Artist("morcheeba")) ]
        entities = e.read([r])
        assert len(entities) == 1
        assert entities[0].artist.name == "morcheeba"
        assert entities[0].name == "trigger hippie"
        assert entities[0].year is None
