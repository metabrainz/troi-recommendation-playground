import json
import unittest
import unittest.mock

import troi
import troi.musicbrainz.genre_lookup

return_json = {
   "00440193-f84c-4e3d-b23c-a96d21c050e6" : {
      "tag" : {
         "artist" : [
            {
               "artist_mbid" : "b8c5cc4f-239f-4e02-b46f-b040b77c2030",
               "count" : 3,
               "tag" : "uk"
            },
            {
               "artist_mbid" : "b8c5cc4f-239f-4e02-b46f-b040b77c2030",
               "count" : 3,
               "genre_mbid" : "54c01942-22fd-4184-9877-1db0089b18f1",
               "tag" : "acid house"
            },
            {
               "artist_mbid" : "b8c5cc4f-239f-4e02-b46f-b040b77c2030",
               "count" : 1,
               "genre_mbid" : "45eb1d9c-588c-4dc8-9394-a14b7c8f02bc",
               "tag" : "trip hop"
            }
         ],
         "recording" : [
            {
               "count" : 3,
               "genre_mbid" : "cc38aba3-48ed-439a-83b9-f81a34a66598",
               "tag" : "downtempo"
            },
            {
               "count" : 3,
               "tag" : "electronic"
            }
         ]
      }
   },
   "0222ff68-4590-49b7-b063-c625e0f735ed" : {
      "tag" : {
         "recording" : [
            {
               "count" : 3,
               "genre_mbid" : "45eb1d9c-588c-4dc8-9394-a14b7c8f02bc",
               "tag" : "trip hop"
            },
            {
               "count" : 3,
               "tag" : "glitch hop"
            },
            {
               "count" : 1,
               "tag" : "glitch"
            }
         ]
      }
   }
}


class TestGenreLookup(unittest.TestCase):

    @unittest.mock.patch('requests.get')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.json = unittest.mock.MagicMock(return_value=return_json)
        req.return_value = mock
        e = troi.musicbrainz.genre_lookup.GenreLookupElement()

        r = [troi.Recording(mbid='00440193-f84c-4e3d-b23c-a96d21c050e6', artist=troi.Artist(name="foo")),
             troi.Recording(mbid='0222ff68-4590-49b7-b063-c625e0f735ed', artist=troi.Artist(name="bar"))]
        entities = e.read([r])
        req.assert_called_with(e.SERVER_URL, params=
            {'recording_mbids': '00440193-f84c-4e3d-b23c-a96d21c050e6,'
                                +'0222ff68-4590-49b7-b063-c625e0f735ed',
             "inc": "tag" 
        })

        assert len(entities) == 2
        assert entities[0].musicbrainz["genre"] == ["downtempo"]
        assert entities[0].musicbrainz["tag"] == ["electronic"]
        assert entities[0].artist.musicbrainz["tag"] == ["uk"]
        assert entities[0].artist.musicbrainz["genre"] == ["acid house"]

        assert entities[1].musicbrainz["genre"] == ["trip hop"]
        assert entities[1].musicbrainz["tag"] == ["glitch hop"]

        assert entities[0].musicbrainz["tag_metadata"] is not None
        assert entities[1].musicbrainz["tag_metadata"] is not None
