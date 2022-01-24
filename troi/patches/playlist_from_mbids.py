from datetime import datetime 
from collections import defaultdict
from urllib.parse import quote
import requests

import click

import troi
from troi import Element, Artist, Recording, Playlist, PipelineError
from troi.musicbrainz.mbid_reader import MBIDReaderElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.playlist import PlaylistMakerElement


@click.group()
def cli():
    pass


class PlaylistFromMBIDsPatch(troi.patch.Patch):
    """
    """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('file_name')
    def parse_args(**kwargs):
        """
        Make a playlist from a file containing one MBID per line.

        \b
        FILE_NAME: filename that contains MBIDS
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "file_name", "desc": "MBID filename", "optional": False }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "playlist-from-mbids"

    @staticmethod
    def description():
        return "Generate a playlist from a list of MBIDSs"

    def create(self, inputs, patch_args):

        source = MBIDReaderElement(inputs['file_name'])

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(source)

        pl_maker = PlaylistMakerElement("Playlist made from MBIDs", "", patch_slug=self.slug())
        pl_maker.set_sources(rec_lookup)

        return pl_maker
