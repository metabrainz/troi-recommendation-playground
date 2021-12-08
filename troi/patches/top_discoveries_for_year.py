from datetime import datetime
import random
import requests

import click

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.listenbrainz.recs
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
import troi.filters
import troi.sorts
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup


@click.group()
def cli():
    pass


class TopDiscoveries(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top discoveries of %d for %s"
    DESC = """<p>
              We generated this playlist from your <a href="https://listenbrainz.org/user/%s/reports?range=year">
              listening statistics for %d</a>. We started with all the recordings that you first listened to in
              %d and then selected the recordings that you listened to more than once. If we found recordings 
              from more than 15 artists, we selected at most 2 recordings from each artist to make this playlist.
              If we found 15 or fewer artists, we picked all the recordings. Finally, we returned at most 30 
              recordings and ordered them by how many times you listened to them in %d.
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
           """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        Generate a top discoveries playlist for a user.

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
        return "top-discoveries-for-year"

    @staticmethod
    def description():
        return "Generate a top discoveries playlist for a user."

    def create(self, inputs, patch_args):
        recs = DataSetFetcherElement(server_url="https://bono.metabrainz.org/top-discoveries/json",
                                     json_post_data=[{ 'user_name': inputs['user_name'] }])

        y_lookup = troi.musicbrainz.year_lookup.YearLookupElement(skip_not_found=False)
        y_lookup.set_sources(recs)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year, inputs['user_name']),
                                                      self.DESC % (inputs['user_name'], year, year, year),
                                                      patch_slug=self.slug())
        pl_maker.set_sources(y_lookup)

        shaper = PlaylistRedundancyReducerElement()
        shaper.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(shaper)

        return shuffle
