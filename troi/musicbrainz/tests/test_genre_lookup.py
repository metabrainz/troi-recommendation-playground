import json
import unittest
import unittest.mock

import troi
import troi.musicbrainz.genre_lookup

return_json = [
   {
      'recording_mbid': '00440193-f84c-4e3d-b23c-a96d21c050e6',
      'genres': 'downtempo',
      'tags': 'downtempo'
   },
   {
      'recording_mbid': '0222ff68-4590-49b7-b063-c625e0f735ed',
      'genres': '',
      'tags': ''
   },
   {
      'recording_mbid': '1636e7a9-229d-446d-aa81-e33071b42d7a',
      'genres': 'hip hop',
      'tags': 'hip hop,hip-hop,hip-hop rap'
   }
]


class TestGenreLookup(unittest.TestCase):

    @unittest.mock.patch('requests.post')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json)
        req.return_value = mock
        e = troi.musicbrainz.genre_lookup.GenreLookupElement()

        r = [troi.Recording(mbid='00440193-f84c-4e3d-b23c-a96d21c050e6'),
             troi.Recording(mbid='0222ff68-4590-49b7-b063-c625e0f735ed'),
             troi.Recording(mbid='1636e7a9-229d-446d-aa81-e33071b42d7a')]
        entities = e.read([r])
        req.assert_called_with(e.SERVER_URL, json=[
            {'[recording_mbid]': '00440193-f84c-4e3d-b23c-a96d21c050e6'},
            {'[recording_mbid]': '0222ff68-4590-49b7-b063-c625e0f735ed'},
            {'[recording_mbid]': '1636e7a9-229d-446d-aa81-e33071b42d7a'}
        ])

        assert len(entities) == 3
        assert entities[0].musicbrainz['tags'] == ['downtempo']
        assert entities[0].musicbrainz['genres'] == ['downtempo']
        assert entities[1].musicbrainz['tags'] == []
        assert entities[1].musicbrainz['genres'] == []
        assert entities[2].musicbrainz['tags'] == ['hip hop', 'hip-hop', 'hip-hop rap']
        assert entities[2].musicbrainz['genres'] == ['hip hop']
