from collections import defaultdict
import requests

import click

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.listenbrainz.stats
import troi.filters
import troi.sorts
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup


@click.group()
def cli():
    pass

class PlaylistMakerElement(Element):
    '''
    '''

    def __init__(self, name, desc):
        super().__init__()
        self.name = name
        self.desc = desc

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):
        print("make playlist '%s' '%s'" % (self.name, self.desc))
        return [Playlist(name=self.name, description=self.desc, recordings=inputs[0])]



class TopTracksYearPatch(troi.patch.Patch):
    """
        See below for description
    """

    def __init__(self, debug=False, max_num_recordings=30):
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

        stats = troi.listenbrainz.stats.UserRecordingElement(user_name=user_name, count=self.max_num_recordings, time_range="year")

        pl_maker = PlaylistMakerElement("Top Recordings of 2020", "These are your top most listened to recordings of 2020.")
        pl_maker.set_sources(stats)

        return pl_maker
