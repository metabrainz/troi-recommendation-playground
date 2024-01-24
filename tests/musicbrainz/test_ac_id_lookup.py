import unittest
import unittest.mock

import troi
import troi.musicbrainz.artist_credit_id_lookup

return_json = """[
    {
        "artist_credit_id": 65,
        "artist_credit_mbids": [
            "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11"
        ],
        "artist_credit_name": "Portishead"
    },
    {
        "artist_credit_id": 197,
        "artist_credit_mbids": [
            "a3cb23fc-acd3-4ce0-8f36-1e5aa6a18432"
        ],
        "artist_credit_name": "U2"
    }
]"""

class TestArtistCreditNameLookup(unittest.TestCase):

    @unittest.mock.patch('requests.get')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = return_json
        req.return_value = mock
        e = troi.musicbrainz.artist_credit_id_lookup.ArtistCreditIdLookupElement()

        inputs = [ troi.Artist(artist_credit_id=65), 
                   troi.Artist(artist_credit_id=197),  
                   troi.Artist(artist_credit_id=3) ]
        entities = e.read([inputs])
        req.assert_called_with(e.SERVER_URL, params={"[artist_credit_id]": "65,197,3"})

        assert len(entities) == 2
        assert entities[0].artist_credit_id == 65
        assert entities[0].name == "Portishead"
        assert entities[0].mbids == ["8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11"]
        assert entities[1].artist_credit_id == 197
        assert entities[1].name == "U2"
        assert entities[1].mbids == ["a3cb23fc-acd3-4ce0-8f36-1e5aa6a18432"]
