import json
import unittest
import unittest.mock

import troi
import troi.musicbrainz.recording_lookup

return_json = {
    "1234a7ae-2af2-4291-aa84-bd0bafe291a1": {
        "artist": {
            "artist_credit_id":
            65,
            "artists": [{
                "area": "United Kingdom",
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "begin_year": 1991,
                "join_phrase": "",
                "name": "Portishead",
                "rels": {
                    "free streaming": "https://www.deezer.com/artist/1069",
                    "lyrics": "https://muzikum.eu/en/122-6105/portishead/lyrics.html",
                    "official homepage": "http://www.portishead.co.uk/",
                    "purchase for download": "https://www.junodownload.com/artists/Portishead/releases/",
                    "social network": "https://www.facebook.com/portishead",
                    "streaming": "https://tidal.com/artist/27441",
                    "wikidata": "https://www.wikidata.org/wiki/Q191352",
                    "youtube": "https://www.youtube.com/user/portishead1002"
                },
                "type": "Group"
            }],
            "name":
            "Portishead"
        },
        "recording": {
            "length":
            253960,
            "name":
            "Sour Times",
            "rels": [{
                "artist_mbid": "5adcb9d9-5ea2-428d-af46-ef626966e106",
                "artist_name": "Beth Gibbons",
                "instrument": "lead vocals",
                "type": "vocal"
            }, {
                "artist_mbid": "eece77f9-9c15-4583-87f8-37d1b7b47e36",
                "artist_name": "Neil Solman",
                "instrument": "Rhodes piano",
                "type": "instrument"
            }, {
                "artist_mbid": "619b1116-740e-42e0-bdfe-96af274f79f7",
                "artist_name": "Adrian Utley",
                "instrument": "guitar",
                "type": "instrument"
            }, {
                "artist_mbid": "eece77f9-9c15-4583-87f8-37d1b7b47e36",
                "artist_name": "Neil Solman",
                "instrument": "Hammond organ",
                "type": "instrument"
            }]
        },
        "release": {
            "album_artist_name": "Portishead",
            "caa_id": 829521842,
            "caa_release_mbid": "76df3287-6cda-33eb-8e9a-044b5e15ffdd",
            "mbid": "76df3287-6cda-33eb-8e9a-044b5e15ffdd",
            "name": "Dummy",
            "release_group_mbid": "48140466-cff6-3222-bd55-63c27e43190d",
            "year": 1994
        },
        "tag": {
            "artist": [{
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 9,
                "genre_mbid": "cc38aba3-48ed-439a-83b9-f81a34a66598",
                "tag": "downtempo"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 12,
                "genre_mbid": "45eb1d9c-588c-4dc8-9394-a14b7c8f02bc",
                "tag": "trip hop"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 6,
                "genre_mbid": "89255676-1f14-4dd8-bbad-fca839d6aff4",
                "tag": "electronic"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 7,
                "tag": "trip-hop"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 1,
                "tag": "the lost generation"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 1,
                "genre_mbid": "6e2e809f-8c54-4e0f-aca0-0642771ab3cf",
                "tag": "electro-industrial"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 4,
                "genre_mbid": "65c97e89-b42b-45c2-a70e-0eca1b8f0ff7",
                "tag": "experimental rock"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 1,
                "genre_mbid": "ec5a14c7-7793-46dc-b858-470183eb63f7",
                "tag": "folktronica"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 3,
                "tag": "british"
            }, {
                "artist_mbid": "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11",
                "count": 2,
                "genre_mbid": "ba318056-9ddf-46cd-8b95-61fc993b962d",
                "tag": "krautrock"
            }],
            "recording": [{
                "count": 3,
                "genre_mbid": "89255676-1f14-4dd8-bbad-fca839d6aff4",
                "tag": "electronic"
            }, {
                "count": 1,
                "genre_mbid": "a2782cb6-1cd0-477c-a61d-b3f8b42dd1b3",
                "tag": "house"
            }, {
                "count": 1,
                "genre_mbid": "7dc2b20f-3953-4874-b9bf-41b8ba06d20c",
                "tag": "acid jazz"
            }, {
                "count": 1,
                "genre_mbid": "ceeaa283-5d7b-4202-8d1d-e25d116b2a18",
                "tag": "alternative rock"
            }, {
                "count": 3,
                "genre_mbid": "cc38aba3-48ed-439a-83b9-f81a34a66598",
                "tag": "downtempo"
            }, {
                "count": 10,
                "genre_mbid": "45eb1d9c-588c-4dc8-9394-a14b7c8f02bc",
                "tag": "trip hop"
            }, {
                "count": 1,
                "genre_mbid": "bab69b07-8bb9-4415-b666-c37609cef80b",
                "tag": "club"
            }, {
                "count": 1,
                "genre_mbid": "e5bba957-8c91-496a-a675-c6d0c6b51c33",
                "tag": "dance"
            }, {
                "count": 4,
                "tag": "trip-hop"
            }],
            "release_group": [{
                "count": 7,
                "tag": "trip-hop"
            }, {
                "count": 1,
                "tag": "british"
            }, {
                "count": 2,
                "tag": "britannique"
            }, {
                "count": 5,
                "genre_mbid": "89255676-1f14-4dd8-bbad-fca839d6aff4",
                "tag": "electronic"
            }, {
                "count": 6,
                "genre_mbid": "cc38aba3-48ed-439a-83b9-f81a34a66598",
                "tag": "downtempo"
            }, {
                "count": 2,
                "genre_mbid": "7dc2b20f-3953-4874-b9bf-41b8ba06d20c",
                "tag": "acid jazz"
            }, {
                "count": 1,
                "genre_mbid": "fd7b5582-e69c-40ad-90b1-d31db33be612",
                "tag": "dark jazz"
            }, {
                "count": 1,
                "genre_mbid": "ec5a14c7-7793-46dc-b858-470183eb63f7",
                "tag": "folktronica"
            }, {
                "count": 1,
                "genre_mbid": "ceeaa283-5d7b-4202-8d1d-e25d116b2a18",
                "tag": "alternative rock"
            }, {
                "count": 1,
                "genre_mbid": "da52c9d1-73f2-456e-a0d0-94bd854cb338",
                "tag": "illbient"
            }, {
                "count": 1,
                "tag": "electronica dance"
            }, {
                "count": 17,
                "genre_mbid": "45eb1d9c-588c-4dc8-9394-a14b7c8f02bc",
                "tag": "trip hop"
            }]
        }
    },
    "ec5b8aa9-7483-4791-a185-1f599a0cdc35": {
        "artist": {
            "artist_credit_id":
            11,
            "artists": [{
                "area": "United States",
                "artist_mbid": "31810c40-932a-4f2d-8cfd-17849844e2a6",
                "begin_year": 1993,
                "join_phrase": "",
                "name": "Squirrel Nut Zippers",
                "rels": {
                    "free streaming": "https://www.deezer.com/artist/7434",
                    "lyrics": "https://genius.com/artists/Squirrel-nut-zippers",
                    "official homepage": "http://snzippers.com/",
                    "social network": "https://www.facebook.com/SNZippers",
                    "streaming": "https://tidal.com/artist/3533610",
                    "wikidata": "https://www.wikidata.org/wiki/Q1817585",
                    "youtube": "https://www.youtube.com/user/snztv"
                },
                "type": "Group"
            }],
            "name":
            "Squirrel Nut Zippers"
        },
        "recording": {
            "length": 275333,
            "name": "Blue Angel",
            "rels": []
        },
        "release": {
            "album_artist_name": "Squirrel Nut Zippers",
            "caa_id": 8413711733,
            "caa_release_mbid": "70fc4df9-1a86-4357-aac7-0694d4248aed",
            "mbid": "70fc4df9-1a86-4357-aac7-0694d4248aed",
            "name": "Hot",
            "release_group_mbid": "c6fe6a2b-0ed6-3d2c-b9ce-ddd5421a3452",
            "year": 1996
        },
        "tag": {
            "artist": [{
                "artist_mbid": "31810c40-932a-4f2d-8cfd-17849844e2a6",
                "count": 3,
                "genre_mbid": "a715278f-1580-409f-8078-4ffbc800e08b",
                "tag": "jazz"
            }, {
                "artist_mbid": "31810c40-932a-4f2d-8cfd-17849844e2a6",
                "count": 1,
                "tag": "american"
            }, {
                "artist_mbid": "31810c40-932a-4f2d-8cfd-17849844e2a6",
                "count": 2,
                "genre_mbid": "6162d71d-6307-4021-8c50-a9524444f645",
                "tag": "swing revival"
            }, {
                "artist_mbid": "31810c40-932a-4f2d-8cfd-17849844e2a6",
                "count": 1,
                "genre_mbid": "063d0461-1e12-4246-87bf-69c5ca611cc2",
                "tag": "swing"
            }],
            "recording": [{
                "count": 1,
                "genre_mbid": "e7bb9a21-9556-4b85-bc78-5f69a3d0577d",
                "tag": "big band"
            }, {
                "count": 2,
                "genre_mbid": "6162d71d-6307-4021-8c50-a9524444f645",
                "tag": "swing revival"
            }, {
                "count": 6,
                "genre_mbid": "a715278f-1580-409f-8078-4ffbc800e08b",
                "tag": "jazz"
            }, {
                "count": 1,
                "genre_mbid": "d017dd87-704b-4ad4-8b67-39fb401b8339",
                "tag": "ragtime"
            }, {
                "count": 4,
                "genre_mbid": "063d0461-1e12-4246-87bf-69c5ca611cc2",
                "tag": "swing"
            }],
            "release_group": [{
                "count": 1,
                "genre_mbid": "d017dd87-704b-4ad4-8b67-39fb401b8339",
                "tag": "ragtime"
            }, {
                "count": 4,
                "genre_mbid": "a715278f-1580-409f-8078-4ffbc800e08b",
                "tag": "jazz"
            }, {
                "count": 2,
                "genre_mbid": "063d0461-1e12-4246-87bf-69c5ca611cc2",
                "tag": "swing"
            }, {
                "count": 1,
                "genre_mbid": "6162d71d-6307-4021-8c50-a9524444f645",
                "tag": "swing revival"
            }]
        }
    }
}


class TestRecordingLookup(unittest.TestCase):

    @unittest.mock.patch('requests.post')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json)
        req.return_value = mock
        e = troi.musicbrainz.recording_lookup.RecordingLookupElement(lookup_tags=True)

        inputs = [
            troi.Recording(mbid="1234a7ae-2af2-4291-aa84-bd0bafe291a1"),
            troi.Recording(mbid="ec5b8aa9-7483-4791-a185-1f599a0cdc35")
        ]
        entities = e.read([inputs])
        req.assert_called_with(e.SERVER_URL,
                               json={
                                   'recording_mbids':
                                   ['1234a7ae-2af2-4291-aa84-bd0bafe291a1', 'ec5b8aa9-7483-4791-a185-1f599a0cdc35'],
                                   'inc': 'artist release tag'
                               },
                               headers={})

        assert len(entities) == 2

        assert entities[0].name == "Sour Times"
        assert entities[0].duration == 253960
        assert entities[0].year == 1994
        assert entities[0].artist_credit.name == "Portishead"
        assert entities[0].artist_credit.artist_credit_id == 65
        assert entities[0].mbid == "1234a7ae-2af2-4291-aa84-bd0bafe291a1"
        assert entities[0].release.mbid == "76df3287-6cda-33eb-8e9a-044b5e15ffdd"
        assert entities[0].release.name == "Dummy"

        # Check tags
        assert entities[0].artist_credit.musicbrainz["genre"] == [
            'downtempo', 'trip hop', 'electronic', 'electro-industrial', 'experimental rock', 'folktronica', 'krautrock'
        ]
        assert entities[0].artist_credit.musicbrainz["tag"] == ['trip-hop', 'the lost generation', 'british']
        assert entities[0].release.musicbrainz["genre"] == [
            'electronic', 'downtempo', 'acid jazz', 'dark jazz', 'folktronica', 'alternative rock', 'illbient', 'trip hop'
        ]
        assert entities[0].release.musicbrainz["tag"] == ['trip-hop', 'british', 'britannique', 'electronica dance']
        assert entities[0].musicbrainz["genre"] == [
            'electronic', 'house', 'acid jazz', 'alternative rock', 'downtempo', 'trip hop', 'club', 'dance'
        ]
        assert entities[0].musicbrainz["tag"] == ['trip-hop']

        assert entities[1].name == "Blue Angel"
        assert entities[1].duration == 275333
        assert entities[1].year == 1996
        assert entities[1].artist_credit.name == "Squirrel Nut Zippers"
        assert entities[1].artist_credit.artist_credit_id == 11
        assert entities[1].mbid == "ec5b8aa9-7483-4791-a185-1f599a0cdc35"
        assert entities[1].release.mbid == "70fc4df9-1a86-4357-aac7-0694d4248aed"
        assert entities[1].release.name == "Hot"

        # Check tags
        assert entities[1].artist_credit.musicbrainz["genre"] == ['jazz', 'swing revival', 'swing']
        assert entities[1].artist_credit.musicbrainz["tag"] == ['american']
        assert entities[1].release.musicbrainz["genre"] == ['ragtime', 'jazz', 'swing', 'swing revival']
        assert entities[1].release.musicbrainz["tag"] == []
        assert entities[1].musicbrainz["genre"] == ['big band', 'swing revival', 'jazz', 'ragtime', 'swing']
        assert entities[1].musicbrainz["tag"] == []
