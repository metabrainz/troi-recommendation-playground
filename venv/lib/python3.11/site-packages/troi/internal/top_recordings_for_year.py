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

    NAME = "Top Recordings of %d for %s"
    DESC = """<p>
              This playlist is made from %s's Top Recordings for %d statistics.
              </p>
              <p>
              We selected the top tracks from this user’s statistics and removed those recordings that we could not
              match to entries in MusicBrainz. (This is a requirement to make this list playable.)
              </p>
              <p>
              This is a review playlist that we hope will give insights into the listening habits of the year.
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        """
        Generate a year in review playlist.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        """
        return [{"type": "argument", "args": ["user_name"]}]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "top-recordings-for-year"

    @staticmethod
    def description():
        return "Generate your year in review playlist."

    def create(self, inputs):
        user_name = inputs['user_name']

        year = datetime.now().year
        stats = troi.listenbrainz.stats.UserRecordingElement(user_name=user_name,
                                                             count=(self.max_num_recordings*2),
                                                             time_range="this_year")

        remove_empty = troi.filters.EmptyRecordingFilterElement()
        remove_empty.set_sources(stats)

        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year, user_name),
                                                      self.DESC % (quote(user_name), year),
                                                      patch_slug=self.slug(),
                                                      user_name=user_name,
                                                      max_num_recordings=self.max_num_recordings)
        pl_maker.set_sources(remove_empty)

        return pl_maker
