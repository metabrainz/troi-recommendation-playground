from datetime import datetime, timedelta
from itertools import zip_longest
import random

import click

from troi import PipelineError, Recording, Playlist
from troi.playlist import PlaylistRedundancyReducerElement, PlaylistMakerElement, PlaylistShuffleElement
import troi.listenbrainz.recs
import troi.filters
import troi.musicbrainz.recording_lookup


@click.group()
def cli():
    pass


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

        raw_recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                              artist_type="raw",
                                                                              count=100)
        raw_recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        raw_recs_lookup.set_sources(raw_recs)

        latest_filter = troi.filters.LatestListenedAtFilterElement(14)
        latest_filter.set_sources(raw_recs_lookup)

        jam_date = datetime.utcnow()
        jam_date = jam_date.strftime("%Y-%m-%d %a")

        pl_maker = PlaylistMakerElement(name="Daily Jams for %s, %s" % (user_name, jam_date),
                                        desc="Daily jams playlist!",
                                        patch_slug=self.slug())
        pl_maker.set_sources(latest_filter)

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(reducer)

        return shuffle
