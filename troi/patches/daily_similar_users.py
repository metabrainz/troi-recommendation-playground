from datetime import datetime, timedelta, timezone
from collections import defaultdict
import random

import click

from troi import PipelineError, Recording, Playlist
from troi.playlist import PlaylistRedundancyReducerElement, PlaylistMakerElement, PlaylistShuffleElement
import troi.listenbrainz.similar_users
import troi.listenbrainz.fetch_listens
import troi.filters
from troi.print_recording import PrintRecordingList


@click.group()
def cli():
    pass

class DailySimilarUsersElement(troi.Element):
    '''
    '''

    def __init__(self, max_tracks_per_user=5):
        '''
        '''
        troi.Element.__init__(self)
        self.max_tracks_per_user = max_tracks_per_user

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs, debug=False):

        recordings = inputs[0]
        users = defaultdict(int)

        results = []
        for rec in recordings:
            if users[rec.musicbrainz["user"]] < self.max_tracks_per_user:
                results.append(rec)

        return results


class DialySimilarUsersPatch(troi.patch.Patch):
    """
    """

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        This patch creates a playlist of a random selection of tracks that users
        who are similar to you have listened to.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        """

        return kwargs

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "daily-similar-users"

    @staticmethod
    def description():
        return """A discovery playlist that consists of track that users similar to yourself
                  listend to in the last day."""

    def create(self, inputs, patch_args):
        user_name = inputs['user_name']

        dt = datetime.utcnow()
        dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0, tzinfo=timezone.utc)
        to_ts = int(dt.timestamp())
        from_ts = to_ts - (60 * 60 * 24)

        user_lookup = troi.listenbrainz.similar_users.SimilarUserLookupElement(user_name)

        listens_lookup = troi.listenbrainz.fetch_listens.FetchListensElement(from_ts, to_ts)
        listens_lookup.set_sources(user_lookup)

        listens_filter = DailySimilarUsersElement(5)
        listens_filter.set_sources(listens_lookup)

        jam_date = datetime.utcnow()
        jam_date = jam_date.strftime("%Y-%m-%d %a")

        pl_maker = PlaylistMakerElement(name="Similar users playlist %s, %s" % (user_name, jam_date),
                                        desc="Similar users playlist!",
                                        patch_slug=self.slug())
        pl_maker.set_sources(listens_filter)

        

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(reducer)

        return shuffle
