from datetime import datetime

import click

from troi import Playlist
from troi.playlist import PlaylistRedundancyReducerElement, PlaylistMakerElement, PlaylistShuffleElement
import troi.listenbrainz.recs
import troi.listenbrainz.listens
import troi.filters
import troi.musicbrainz.recording_lookup


@click.group()
def cli():
    pass


DAYS_OF_RECENT_LISTENS_TO_EXCLUDE = 14  # Exclude tracks listened in last X days from the daily jams playlist


class DailyJamsPatch(troi.patch.Patch):
    """
        Taken a list of Recordings, break them into 7 roughly equal chunks and return
        the chunk for the given day of the week.
    """

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    @click.argument('jam_date', required=False)
    def parse_args(**kwargs):
        """
        Generate a daily playlist from the ListenBrainz recommended recordings.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        JAM_DATE is the date for which the jam is created (this is needed to account for the fact different timezones
        can be on different dates). Recommended formatting for the date is 'YYYY-MM-DD DAY_OF_WEEK'.
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

    def create(self, inputs):
        user_name = inputs['user_name']
        jam_date = inputs.get('jam_date')
        if jam_date is None:
            jam_date = datetime.utcnow().strftime("%Y-%m-%d %a")

        raw_recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                              artist_type="raw",
                                                                              count=100)
        raw_recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        raw_recs_lookup.set_sources(raw_recs)

        recent_listens_lookup = troi.listenbrainz.listens.RecentListensTimestampLookup(user_name, days=2)
        recent_listens_lookup.set_sources(raw_recs_lookup)

        latest_filter = troi.filters.LatestListenedAtFilterElement(DAYS_OF_RECENT_LISTENS_TO_EXCLUDE)
        latest_filter.set_sources(recent_listens_lookup)

        pl_maker = PlaylistMakerElement(name="Daily Jams for %s, %s" % (user_name, jam_date),
                                        desc="Daily jams playlist!",
                                        patch_slug=self.slug())
        pl_maker.set_sources(latest_filter)

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(reducer)

        return shuffle
