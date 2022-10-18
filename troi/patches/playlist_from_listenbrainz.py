import click

from troi import Playlist
from troi.playlist import PlaylistFromJSPFElement
import troi.musicbrainz.recording_lookup


@click.group()
def cli():
    pass


class TransferPlaylistPatch(troi.patch.Patch):

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument("mbid")
    @click.argument("read_only_token", required=False)
    def parse_args(**kwargs):
        """
        A dummy patch that retrieves an existing playlist from ListenBrainz.

        \b
        MBID is the playlist mbid to save again.
        READ_ONLY_TOKEN is the listenbrainz auth token to retrieve the playlist if its private. If not specified,
        fallback to TOKEN. Both arguments take the same value but specifying TOKEN may also upload the playlist
        to LB again which is many times not desirable.
        """
        return kwargs

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
        token = inputs.get("read_only_token")
        if not token:
            token = inputs.get("token")
        playlist = PlaylistFromJSPFElement(inputs["mbid"], token)
        return playlist
