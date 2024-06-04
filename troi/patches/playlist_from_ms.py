import json

from troi import Playlist
from troi.patch import Patch
from troi.playlist import RecordingsFromMusicServiceElement, PlaylistMakerElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement


class ImportPlaylistPatch(Patch):

    @staticmethod
    def inputs():
        """
        A patch that retrieves an existing playlist from Spotify for use in Troi.

        \b
        TOKEN is the music service token from which the playlist is retrieved. For now, only Spotify tokens are accepted. 
        PLAYLIST_ID is the playlist id to retrieve the tracks from it.
        """
        return [
            {"type": "argument", "args": ["token"], "kwargs": {"required": False}},
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

        token = inputs["token"]
        playlist_id = inputs["playlist_id"]

        token = inputs.get("lb_token")
        source = RecordingsFromMusicServiceElement(token=token, playlist_id=playlist_id)
        
        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(source)

        pl_maker = PlaylistMakerElement("Playlist made from MBIDs", "", patch_slug=self.slug())
        pl_maker.set_sources(rec_lookup)

        return pl_maker
