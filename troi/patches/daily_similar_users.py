from datetime import datetime, timedelta
from itertools import zip_longest
import random

import click

from troi import PipelineError, Recording, Playlist
from troi.playlist import PlaylistRedundancyReducerElement, PlaylistMakerElement, PlaylistShuffleElement
import troi.listenbrainz.similar_users
import troi.listenbrainz.fetch_listens
import troi.filters


@click.group()
def cli():
    pass


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

        URL = "https://api.listenbrainz.org/1/%s/similar-users"

        r = requests.get(self.URL % user_name)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch recording tags from MusicBrainz: HTTP code %d" % r.status_code)

        for user in r.json()["payload"]:
        users = troi.listenbrainz.similar_users.SimilarUserLookupElement(user_name)

        listens_lookup = troi.listenbrainz.fetch_listens.FetchListensElement(


        jam_date = datetime.utcnow()
        jam_date = jam_date.strftime("%Y-%m-%d %a")

        pl_maker = PlaylistMakerElement(name="Similar users playlist %s, %s" % (user_name, jam_date),
                                        desc="Similar users playlist!",
                                        patch_slug=self.slug())
        pl_maker.set_sources(listens)

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(reducer)

        return shuffle
