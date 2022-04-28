from datetime import datetime, timedelta
import random

import click

from troi import Element, PipelineError, Recording, Playlist
import troi.listenbrainz.recs
import troi.filters
import troi.musicbrainz.recording_lookup


@click.group()
def cli():
    pass


class DailyJamsElement(Element):
    '''
        Split weekly recommended recordings into 7 sets, one for each day of the week.
    '''

    def __init__(self, recs, user, day, slug):
        Element.__init__(self)
        self.recs = recs
        self.user = user
        self.day = day
        self.slug = slug

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):
        recordings = inputs[0]
        if not recordings or len(recordings) == 0:
            return []

        random.seed(self.recs.last_updated)
        random.shuffle(recordings)
        num_per_day = len(recordings) // 7
        days = [recordings[i:i + num_per_day] for i in range(0, len(recordings), num_per_day)]

        jam_date = datetime.utcnow() - timedelta(days=datetime.utcnow().isoweekday() % 7)
        jam_date += timedelta(days=self.day)
        jam_date = jam_date.strftime("%Y-%m-%d %a")

        return [ Playlist(name="Daily Jams for %s, %s" % (self.user, jam_date),
                          recordings=days[self.day - 1],
                          patch_slug=self.slug) ]


class DailyJamsPatch(troi.patch.Patch):
    """
        Taken a list of Recordings, break them into 7 roughly equal chunks and return
        the chunk for the given day of the week.
    """

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    @click.argument('type')
    @click.argument('day', required=False, type=int)
    def parse_args(**kwargs):
        """
        Generate a daily playlist from the ListenBrainz recommended recordings.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        TYPE is The type of daily jam. Must be 'top' or 'similar'.
        DAY is The day of the week to generate jams for (1 = Monday, 2 = Tuesday, 7 = Sunday). Leave blank for today.
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
        return "Generate a daily playlist from the ListenBrainz recommended recordings. Day 1 = Monday, Day 2  = Tuesday ..."

    def create(self, inputs, patch_args):
        user_name = inputs['user_name']
        type = inputs['type']
        day = inputs['day']
        if day is None:
            day = 0

        if day > 7:
            raise PipelineError("day must be an integer between 0-7.")
        if day == 0:
            day = datetime.today().weekday() + 1

        if type not in ("top", "similar"):
            raise PipelineError("type must be either 'top' or 'similar'")


        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                          artist_type=type,
                                                                          count=-1)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(recs)

        # If an artist should never appear in a playlist, add the artist_credit_id here
        artist_filter = troi.filters.ArtistCreditFilterElement([])
        artist_filter.set_sources(r_lookup)

        if type == "top":
            artist_limiter = troi.filters.ArtistCreditLimiterElement(count=9)
        else:
            artist_limiter = troi.filters.ArtistCreditLimiterElement(count=3)
        artist_limiter.set_sources(artist_filter)

        jams = DailyJamsElement(recs, user=user_name, day=day, slug=DailyJamsPatch.slug())
        jams.set_sources(artist_limiter)

        return jams
