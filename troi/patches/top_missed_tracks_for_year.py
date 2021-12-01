from datetime import datetime 
from collections import defaultdict
from urllib.parse import quote
import requests

import click

import troi
from troi import Element, Artist, Recording, Playlist, PipelineError
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.acousticbrainz.mood_lookup import MoodLookupElement
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement


@click.group()
def cli():
    pass


class TopMissedTracksPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top Missed recordings for %s"
    DESC = """<p>
              This playlist is made from tracks that your most similar users listened to this year, but that
              you didn't listen to this year.
              </p>
              <p>
              Double click on any recording to start playing it -- we'll do our best to find a matching recording
              to play. If you have Spotify, we recommend connecting your account for a better playback experience.
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        Generate a top missed tracks playlists for a given user.

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
        return "top-missed-recordings"

    @staticmethod
    def description():
        return "Generate a playlist from the top tracks that the most similar users listened to, but the user didn't listen to."

    def create(self, inputs):
        source = DataSetFetcherElement(server_url="https://bono.metabrainz.org/top-missed-tracks/json",
                                       json_post_data=[{ 'user_name': inputs['user_name'] }])

        mood_lookup = MoodLookupElement()
        mood_lookup.set_sources(source)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % inputs['user_name'],
                                                      self.DESC)
        pl_maker.set_sources(mood_lookup)

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        return pl_maker
