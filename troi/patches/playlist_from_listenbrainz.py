import click

from troi import Playlist
from troi.playlist import PlaylistFromJSPFElement
import troi.musicbrainz.recording_lookup


@click.group()
def cli():
    pass


class ResavePatch(troi.patch.Patch):

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument("mbid")
    @click.argument("token", required=False)
    def parse_args(**kwargs):
        """
        A dummy patch that retrieves an existing playlist from ListenBrainz.

        \b
        MBID is the playlist mbid to save again.
        TOKEN is the listenbrainz auth token to retrieve the playlist if its private.
        """

        return kwargs

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "resave-playlist"

    @staticmethod
    def description():
        return "Retrieve a playlist from the ListenBrainz"

    def create(self, inputs, patch_args):
        token = inputs.get("token")
        if not token:
            token = patch_args.get("token")
        playlist = PlaylistFromJSPFElement(inputs["mbid"], token)
        return playlist
