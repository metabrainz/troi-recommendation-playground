import json

from troi import Playlist
from troi.patch import Patch
from troi.playlist import RecordingsFromMusicServiceElement, PlaylistMakerElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.tools.spotify_lookup import get_tracks_from_playlist


class ImportPlaylistPatch(Patch):

    @staticmethod
    def inputs():
        """
        A patch that retrieves an existing playlist from Spotify for use in Troi.

        \b
        MS_TOKEN is the music service token from which the playlist is retrieved. For now, only Spotify tokens are accepted. 
        PLAYLIST_ID is the playlist id to retrieve the tracks from it.
        """
        return [
            {"type": "argument", "args": ["ms_token"], "kwargs": {"required": False}},
            {"type": "argument", "args": ["playlist_id"], "kwargs": {"required": False}},
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "import-playlist"

    @staticmethod
    def description():
        return "Retrieve a playlist from the Spotify"

    def create(self, inputs):

        ms_token = inputs["ms_token"]
        playlist_id = inputs["playlist_id"]
        
        _, name, desc = get_tracks_from_playlist(ms_token, playlist_id)

        source = RecordingsFromMusicServiceElement(token=ms_token, playlist_id=playlist_id)
        
        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(source)

        pl_maker = PlaylistMakerElement(name, desc, patch_slug=self.slug())
        pl_maker.set_sources(rec_lookup)

        return pl_maker
