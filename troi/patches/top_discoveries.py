from datetime import datetime
import random
import requests

import click

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.listenbrainz.recs
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
import troi.filters
import troi.sorts
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup
import troi.patches.top_tracks_for_year


@click.group()
def cli():
    pass


class TopDiscoveries(troi.patch.Patch):
    """
        See below for description
    """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        Generate a top discoveries playlist for a user.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "user_name", "desc": "ListenBrainz user name", "optional": False }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "top-discoveries"

    @staticmethod
    def description():
        return "Generate a top discoveries playlist for a user."

    def create(self, inputs):
        recs = DataSetFetcherElement(server_url="https://bono.metabrainz.org/top-discoveries/json",
                                     json_post_data=[{ 'user_name': inputs['user_name'] }])

        y_lookup = troi.musicbrainz.year_lookup.YearLookupElement(skip_not_found=False)
        y_lookup.set_sources(recs)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement("Top discoveries of %s" % year,
                                                                         "Top tracks you started listening to in %s." % year)
        pl_maker.set_sources(y_lookup)

        shaper = PlaylistRedundancyReducerElement()
        shaper.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(shaper)

        return shuffle
