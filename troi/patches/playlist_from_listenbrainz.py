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
    def parse_args(**kwargs):
        """
        A dummy patch that retrieves an existing playlist from ListenBrainz.

        \b
        MBID is the playlist mbid to save again.
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
        playlist = PlaylistFromJSPFElement(inputs["mbid"], patch_args.get("token"))
        return playlist
