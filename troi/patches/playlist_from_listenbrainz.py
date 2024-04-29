import json

from troi import Playlist
from troi.patch import Patch
from troi.playlist import PlaylistFromJSPFElement


class TransferPlaylistPatch(Patch):

    @staticmethod
    def inputs():
        """
        A dummy patch that retrieves an existing playlist from ListenBrainz or raw JSPF for use in Troi.

        \b
        MBID is the playlist mbid to save. Specify this OR JSPF.
        JSPF is the actual JSPF playlist to transfer. Specify this OR MBID.
        READ_ONLY_TOKEN is the listenbrainz auth token to retrieve the playlist if its private. If not specified,
        fallback to TOKEN. Both arguments take the same value but specifying TOKEN may also upload the playlist
        to LB again which is many times not desirable.
        """
        return [
            {"type": "argument", "args": ["mbid"], "kwargs": {"required": False}},
            {"type": "argument", "args": ["jspf"], "kwargs": {"required": False}},
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

        mbid = inputs["mbid"]
        jspf = inputs["jspf"]

        if mbid == "":
            mbid = None
        if jspf == "":
            jspf = None

        if mbid is not None and jspf is not None:
            raise RuntimeError("Cannot pass both playlist mbid and jspf to TransferPlaylistPatch.")

        if mbid is None and jspf is None:
            raise RuntimeError("Must pass either playlist mbid or jspf to TransferPlaylistPatch.")

        if isinstance(jspf, str):
            jspf = json.loads(jspf)

        token = inputs.get("read_only_token") or inputs.get("token")
        return PlaylistFromJSPFElement(playlist_mbid=mbid, jspf=jspf, token=token)
