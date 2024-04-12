import unittest
import unittest.mock

import troi
import troi.musicbrainz.related_artist_credits

return_json = [
    {
        "artist_credit_id": 65,
        "artist_credit_name": "Portishead",
        "count": 64,
        "related_artist_credit_id": 20660,
        "related_artist_credit_name": "Oasis"
    },
    {
        "artist_credit_id": 963,
        "artist_credit_name": "Morcheeba",
        "count": 120,
        "related_artist_credit_id": 359,
        "related_artist_credit_name": "Moby"
    }
]

class TestArtistCreditNameLookup(unittest.TestCase):

    @unittest.mock.patch('requests.get')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = return_json
        req.return_value = mock
        e = troi.musicbrainz.related_artist_credits.RelatedArtistCreditsElement()

        inputs = [ troi.ArtistCredit(artist_credit_id=65), 
                   troi.ArtistCredit(artist_credit_id=963) ]
        entities = e.read([inputs])
        req.assert_called_with(e.SERVER_URL, params={'[artist_credit_id]': '65,963', 'threshold': 0})

        assert len(entities) == 2
        assert entities[0].artist_credit_id == 65
        assert entities[1].artist_credit_id == 963
        assert len(entities[0].musicbrainz['related_artist_credit_ids']) == 1

        assert entities[0].musicbrainz['related_artist_credit_ids'][0]['artist_credit_id'] == 65
        assert entities[0].musicbrainz['related_artist_credit_ids'][0]['artist_credit_name'] == 'Portishead'
        assert entities[0].musicbrainz['related_artist_credit_ids'][0]['related_artist_credit_id'] == 20660
        assert entities[0].musicbrainz['related_artist_credit_ids'][0]['related_artist_credit_name'] == 'Oasis'

        assert len(entities[1].musicbrainz['related_artist_credit_ids']) == 1
        assert entities[1].musicbrainz['related_artist_credit_ids'][0]['artist_credit_id'] == 963
        assert entities[1].musicbrainz['related_artist_credit_ids'][0]['artist_credit_name'] == 'Morcheeba'
        assert entities[1].musicbrainz['related_artist_credit_ids'][0]['related_artist_credit_id'] == 359
        assert entities[1].musicbrainz['related_artist_credit_ids'][0]['related_artist_credit_name'] == 'Moby'
