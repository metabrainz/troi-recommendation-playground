from datetime import datetime 
from collections import defaultdict
import requests

import click

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.listenbrainz.stats
import troi.filters
import troi.sorts
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup


@click.group()
def cli():
    pass


class TopTracksYouListenedToPatch(troi.patch.Patch):
    """
        See below for description
    """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        Generate a playlist that contains a mix of tracks released this year that you've
        listened to.

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
        return "top-new-recordings-for-year"

    @staticmethod
    def description():
        return "Generate a playlist of tracks released this year that you've listened to."

    def create(self, inputs):
        recs = DataSetFetcherElement(server_url="https://bono.metabrainz.org/top-new-tracks/json",
                                     json_post_data=[{ 'user_name': inputs['user_name'] }])

        y_lookup = troi.musicbrainz.year_lookup.YearLookupElement(skip_not_found=False)
        y_lookup.set_sources(recs)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement("Tracks released in %s you've listened to." % year,
                         "Tracks that were released in %s and you've listened to. (Yes, we finish sentences with prepositions here.)" % year)
        pl_maker.set_sources(recs)

        shaper = PlaylistRedundancyReducerElement()
        shaper.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(shaper)

        return shuffle
