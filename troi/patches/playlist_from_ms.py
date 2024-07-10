import json

from troi import Playlist
from troi.patch import Patch
from troi.playlist import RecordingsFromMusicServiceElement, PlaylistMakerElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.tools.apple_lookup import get_tracks_from_apple_playlist
from troi.tools.spotify_lookup import get_tracks_from_spotify_playlist


class ImportPlaylistPatch(Patch):

    @staticmethod
    def inputs():
        """
        A patch that retrieves an existing playlist from Spotify/Apple Music/SoundCloud for use in Troi.

        \b
        MS_TOKEN is the music service token from which the playlist is retrieved. For now, only Spotify tokens are accepted. 
        PLAYLIST_ID is the playlist id to retrieve the tracks from it.
        MUSIC_SERVICE is the music service from which the playlist is retrieved
        APPLE_USER_TOKEN is the apple user token. Optional, if music services is not Apple Music
        """
        return [
            {"type": "argument", "args": ["ms_token"], "kwargs": {"required": False, "help-text": "The music service token from which the playlist is retrieved. For now, only Spotify tokens are accepted." }},
            {"type": "argument", "args": ["playlist_id"], "kwargs": {"required": False, "help-text": "The playlist id to retrieve the tracks from it"}},
            {"type": "argument", "args": ["music_service"], 
                "kwargs": {
                    "required": False, 
                    "help-text": "The music service from which the playlist is retrieved : Spotify/Apple Music/SoundCloud",
                    "choices": ["Spotify", "Apple Music", "SoundCloud"]
                    }},
            {"type": "argument", "args": ["apple_user_token"], "kwargs": {"required": False, "help-text": "The apple user token. Optional, if music services is not Apple Music"}},
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
        
        # this one only used to get track name and desc
        if music_service == "spotify":
            tracks, name, desc = get_tracks_from_spotify_playlist(ms_token, playlist_id)
        elif music_service == "apple_music":
            tracks, name, desc = get_tracks_from_apple_playlist(ms_token, apple_user_token, playlist_id)

        source = RecordingsFromMusicServiceElement(token=ms_token, playlist_id=playlist_id, music_service=music_service, apple_user_token=apple_user_token)
        
        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(source)

        pl_maker = PlaylistMakerElement(name, desc, patch_slug=self.slug())
        pl_maker.set_sources(rec_lookup)

        return pl_maker
