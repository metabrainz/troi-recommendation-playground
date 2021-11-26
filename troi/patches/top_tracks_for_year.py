from datetime import datetime 
from collections import defaultdict
from urllib.parse import quote
import requests

import click

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.listenbrainz.stats
import troi.filters
import troi.sorts
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.mbid_mapping


@click.group()
def cli():
    pass


class TopTracksYearPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top recordings of 2020 for %s"
    DESC = """<p>
              This playlist is made from your <a href="https://listenbrainz.org/user/%s/reports?range=year">
              top recordings for 2020 statistics</a>.
              </p>
              <p>
              Double click on any recording to start playing it -- we'll do our best to find a matching recording
              to play. If you have Spotify, we recommend connecting your account for a better playback experience.
              </p>
              <p>
              Please keep in mind that this is our first attempt at making playlists for our users. Our processes
              are not fully debugged and you may find that things are not perfect. So, if this playlist isn't
              very accurate, we apologize -- we'll continue to make them better. (e.g. some recordings may be missing
              from this list because we were not able to find a match for it in MusicBrainz.)
              </p>
              <p>
              Happy holidays from everyone at MetaBrainz!
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
        Generate a year in review playlist.

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
        return "year-top-recordings"

    @staticmethod
    def description():
        return "Generate your year in review playlist."

    def create(self, inputs):
        user_name = inputs['user_name']

        year = datetime.now().year
        stats = troi.listenbrainz.stats.UserRecordingElement(user_name=user_name, count=self.max_num_recordings, time_range="year")

        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % user_name, self.DESC % quote(user_name))
        pl_maker.set_sources(stats)

        return pl_maker
