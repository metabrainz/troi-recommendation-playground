from datetime import datetime, timedelta
from itertools import zip_longest
import random

import click

from troi import Element, PipelineError, Recording, Playlist
from troi.playlist import PlaylistRedundancyReducerElement, PlaylistMakerElement, PlaylistShuffleElement
import troi.listenbrainz.recs
import troi.filters
import troi.musicbrainz.recording_lookup


@click.group()
def cli():
    pass


class ZipperElement(Element):
    '''
        Given two or more inputs, pick recordings from each alternatingly
    '''

    def __init__(self):
        Element.__init__(self)

    @staticmethod
    def inputs():
        return [Recording, Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        output = []
        for rec0, rec1 in zip_longest(inputs[0], inputs[1]):
            if rec0 is not None:
                output.append(rec0)
            if rec1 is not None:
                output.append(rec1)

        return output


class DailyJamsPatch(troi.patch.Patch):
    """
        Taken a list of Recordings, break them into 7 roughly equal chunks and return
        the chunk for the given day of the week.
    """

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        Generate a daily playlist from the ListenBrainz recommended recordings.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        """

        return kwargs

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "daily-jams"

    @staticmethod
    def description():
        return "Generate a daily playlist from the ListenBrainz recommended recordings."

    def create(self, inputs, patch_args):
        user_name = inputs['user_name']

        top_recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                              artist_type="top",
                                                                              count=100)
        top_recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        top_recs_lookup.set_sources(top_recs)

        sim_recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                              artist_type="similar",
                                                                              count=100)
        sim_recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        sim_recs_lookup.set_sources(sim_recs)

        zipper = ZipperElement()
        zipper.set_sources([top_recs_lookup, sim_recs_lookup])

        jam_date = datetime.utcnow()
        jam_date = jam_date.strftime("%Y-%m-%d %a")

        pl_maker = PlaylistMakerElement(name="Daily Jams for %s, %s" % (user_name, jam_date),
                                        desc="Daily jams playlist!",
                                        patch_slug=self.slug)
        pl_maker.set_sources(zipper)

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(reducer)

        return shuffle
