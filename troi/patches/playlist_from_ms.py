import json

from troi import Playlist
from troi.patch import Patch
from troi.playlist import RecordingsFromMusicServiceElement, PlaylistMakerElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.tools.apple_lookup import get_tracks_from_apple_playlist
from troi.tools.spotify_lookup import get_tracks_from_spotify_playlist
from troi.tools.soundcloud_lookup import get_soundcloud_playlist


class ImportPlaylistPatch(Patch):

    @staticmethod
    def inputs():
        """
        A patch that retrieves an existing playlist from Spotify for use in Troi.

        \b
        MS_TOKEN is the music service token from which the playlist is retrieved. For now, only Spotify tokens are accepted. 
        PLAYLIST_ID is the playlist id to retrieve the tracks from it.
        MUSIC_SERVICE is the music service from which the playlist is retrieved
        APPLE_USER_TOKEN is the apple user token. Optional, if music service is not Apple Music
        """
        return [
            {"type": "argument", "args": ["ms_token"], "kwargs": {"required": False}},
            {"type": "argument", "args": ["playlist_id"], "kwargs": {"required": False}},
            {"type": "argument", "args": ["music_service"], "kwargs": {"required": False}},
            {"type": "argument", "args": ["apple_user_token"], "kwargs": {"required": False}},
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "import-playlist"

    @staticmethod
    def description():
        return "Retrieve a playlist from the Music Services (Spotify/Apple Music/SoundCloud)"

    def create(self, inputs):

        ms_token = inputs["ms_token"]
        playlist_id = inputs["playlist_id"]
        music_service = inputs["music_service"]
        apple_user_token = inputs["apple_user_token"]

        if apple_user_token == "":
            apple_user_token = None

        if music_service == "apple_music" and apple_user_token is None:
            raise RuntimeError("Authentication is required")

        playlist_fetchers = {
            "spotify": get_tracks_from_spotify_playlist,
            "apple_music": get_tracks_from_apple_playlist,
            "soundcloud": get_soundcloud_playlist
        }

        get_tracks = playlist_fetchers.get(music_service)
        if not get_tracks:
            raise ValueError(f"Unsupported music service: {music_service}")

        _, name, desc = get_tracks(ms_token, apple_user_token, playlist_id) if music_service == "apple_music" else get_tracks(ms_token, playlist_id)

        source = RecordingsFromMusicServiceElement(token=ms_token, playlist_id=playlist_id, music_service=music_service, apple_user_token=apple_user_token)
        
        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(source)

        pl_maker = PlaylistMakerElement(name, desc, patch_slug=self.slug())
        pl_maker.set_sources(rec_lookup)

        return pl_maker
