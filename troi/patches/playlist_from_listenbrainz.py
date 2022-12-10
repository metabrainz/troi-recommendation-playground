from troi import Playlist
from troi.playlist import PlaylistFromJSPFElement
import troi.musicbrainz.recording_lookup


class TransferPlaylistPatch(troi.patch.Patch):

    @staticmethod
    def inputs():
        """
        A dummy patch that retrieves an existing playlist from ListenBrainz.

        \b
        MBID is the playlist mbid to save again.
        READ_ONLY_TOKEN is the listenbrainz auth token to retrieve the playlist if its private. If not specified,
        fallback to TOKEN. Both arguments take the same value but specifying TOKEN may also upload the playlist
        to LB again which is many times not desirable.
        """
        return [
            {"type": "argument", "args": ["mbid"]},
            {"type": "argument", "args": ["read_only_token"], "kwargs": {"required": False}}
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "transfer-playlist"

    @staticmethod
    def description():
        return "Retrieve a playlist from the ListenBrainz"

    def create(self, inputs):
        token = inputs.get("read_only_token") or inputs.get("token")
        return PlaylistFromJSPFElement(inputs["mbid"], token)
