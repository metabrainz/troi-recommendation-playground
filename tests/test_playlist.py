import unittest

import requests_mock

from troi.patch import Patch
from troi import Recording, Element, Playlist
from troi.tools.spotify_lookup import SPOTIFY_IDS_LOOKUP_URL


class DummyElement(Element):
    """ Dummy element that returns a fixed playlist for testing """

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, sources):
        recordings = [
            Recording(name="I Want It That Way", mbid="87dfa566-21c3-45ed-bc42-1d345b8563fa"),
            Recording(name="Untouchable"),
            Recording(name="The Perfect Kiss", mbid="ec0da94e-fbfe-4eb0-968e-024d4c32d1d0"),
            Recording(name="Love Your Voice", mbid="93726547-f8c0-4efd-8e16-d2dee76500f6"),
            Recording(name="Hall of Fame", mbid="395bd5a1-79cc-4e04-8869-ca9eabc78d09"),
        ]
        return [
            Playlist(
                name="Test Export Playlist",
                description="A playlist to test exporting playlists to spotify",
                recordings=recordings
            )
        ]


class DummyPatch(Patch):
    """ Dummy patch that always returns a fixed set of recordings for testing """

    @staticmethod
    def slug():
        return "test-patch"

    def create(self, inputs):
        return DummyElement()

    @staticmethod
    def outputs():
        return [Recording]


class TestSpotifySubmission(unittest.TestCase):

    @requests_mock.Mocker()
    def test_submit_to_spotify(self, mock_requests):
        self.maxDiff = None
        playlist_id = "33DUxaq2HQI7PDFODpFWJV"
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"

        mock_requests.post(SPOTIFY_IDS_LOOKUP_URL, json=[
            {
                "artist_name": "Backstreet Boys",
                "recording_mbid": "87dfa566-21c3-45ed-bc42-1d345b8563fa",
                "release_name": "Millennium",
                "spotify_track_ids": ["47BBI51FKFwOMlIiX6m8ya"],
                "track_name": "I Want It That Way"
            },
            {
                "artist_name": "New Order",
                "recording_mbid": "ec0da94e-fbfe-4eb0-968e-024d4c32d1d0",
                "release_name": "Low‐Life",
                "spotify_track_ids": ["7y9bltr6hV3CsbqXWgwVZv", "4LWQfAhwP1Tf1wbzmT6NwW", "7clvpmRL6Ga8OyOs0is5RP"],
                "track_name": "The Perfect Kiss"
            },
            {
                "artist_name": "JONY",
                "recording_mbid": "93726547-f8c0-4efd-8e16-d2dee76500f6",
                "release_name": "Список твоих мыслей",
                "spotify_track_ids": ["4hyVrAsoKKjxAvQjPRt0ai", "75VNPADAFa4iNpjEBUYMhF"],
                "track_name": "Love Your Voice"
            },
            {
                "artist_name": "The Script featuring will.i.am",
                "recording_mbid": "395bd5a1-79cc-4e04-8869-ca9eabc78d09",
                "release_name": "#3",
                "spotify_track_ids": [],
                "track_name": "Hall of Fame"
            }
        ])

        mock_requests.post("https://api.spotify.com/v1/users/test-user-id/playlists", json={
            "id": playlist_id,
            "external_urls": {
                "spotify": playlist_url
            }
        })

        mock_requests.put(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", json={"snapshot_id": "baz"})

        mock_requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", json={"snapshot_id": "foo"})

        mock_requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", json={
            "items": [
                {
                    "track": {
                        "name": "Backstreet Boys",
                        "id": "47BBI51FKFwOMlIiX6m8ya",
                        "is_playable": True
                    }
                },
                {
                    "track": {
                        "name": "New Order",
                        "id": "7y9bltr6hV3CsbqXWgwVZv",
                        "is_playable": False
                    }
                },
                {
                    "track": {
                        "name": "Love Your Voice",
                        "id": "4hyVrAsoKKjxAvQjPRt0ai",
                        "is_playable": True
                    }
                }
            ]
        })

        # the New Order track is unplayable and its alternative track ids should be rechecked
        mock_requests.get(
            f"https://api.spotify.com/v1/tracks/?ids=4LWQfAhwP1Tf1wbzmT6NwW,7clvpmRL6Ga8OyOs0is5RP&market=from_token",
            complete_qs=True,  # complete_qs to ensure that the track ids being rechecked are the exact ones we want
            json={
                "tracks": [
                    {
                        "id": "4LWQfAhwP1Tf1wbzmT6NwW",
                        "is_playable": True
                    },
                    {
                        "id": "7clvpmRL6Ga8OyOs0is5RP",
                        "is_playable": True
                    }
                ]
            }
        )
        mock_requests.put(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", json={"snapshot_id": "bar"})

        patch = DummyPatch({
            "min_recordings": 1,
            "spotify": {
                "token": "spotify-auth-token",
                "user_id": "test-user-id",
                "is_public": True,
                "is_collaborative": False
            },
            "name": "Test Export Playlist",
            "upload": True
        })
        playlist = patch.generate_playlist()

        history = mock_requests.request_history

        # track 2 in playlist doesn't have a mbid and is skipped from request to lookup track ids
        self.assertEqual(history[0].json(), [
            {"recording_mbid": "87dfa566-21c3-45ed-bc42-1d345b8563fa"},
            {"recording_mbid": "ec0da94e-fbfe-4eb0-968e-024d4c32d1d0"},
            {"recording_mbid": "93726547-f8c0-4efd-8e16-d2dee76500f6"},
            {"recording_mbid": "395bd5a1-79cc-4e04-8869-ca9eabc78d09"}
        ])

        self.assertEqual(history[1].json(), {
            "name": "Test Export Playlist",
            "description": "A playlist to test exporting playlists to spotify",
            "public": True,
            "collaborative": False
        })

        # we had 4 tracks with mbids, out of those no matching spotify id was found for the last track id.
        # so we submitted the first spotify track id for the remaining tracks preserving the order in which
        # occur in the original playlist
        self.assertEqual(history[2].json(), [
            "spotify:track:47BBI51FKFwOMlIiX6m8ya",
            "spotify:track:7y9bltr6hV3CsbqXWgwVZv",
            "spotify:track:4hyVrAsoKKjxAvQjPRt0ai"
        ])

        # history[3] is the request to retrieve tracks for checking whether the playlist has unplayable tracks
        # history[4] is the request to retrieve info for alternative spotify ids of unplayable tracks, only thing
        # to check about this is the query strings which the request matcher in the beginning of this method does
        # history[5] is the request to reset the playlist tracks

        # we had found one track to be unplayable and replaced it with an alternative playable track. now updating the
        # playlist again so check the all the correct tracks and the new replaced tracks are sent and also in the
        # original order in which the tracks occur in the playlist
        self.assertEqual(history[6].json(), [
            "spotify:track:47BBI51FKFwOMlIiX6m8ya",
            "spotify:track:4LWQfAhwP1Tf1wbzmT6NwW",
            "spotify:track:4hyVrAsoKKjxAvQjPRt0ai"
        ])

        self.assertEqual(playlist.playlists[0].additional_metadata["external_urls"]["spotify"], playlist_url)
