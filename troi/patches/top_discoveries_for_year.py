from datetime import datetime

import troi.filters
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup
import troi.sorts
from troi import Recording
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.playlist import PlaylistShuffleElement, PlaylistMakerElement


class TopDiscoveries(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top Discoveries of %d for %s"
    DESC = """<p>
              This playlist contains the top tracks for %s that were first listened to in %d.
              </p>
              <p>
                For more information on how this playlist is generated, please see our
                <a href="https://musicbrainz.org/doc/YIM2022Playlists">Year in Music 2022 Playlists</a> page.
              </p>
           """

    def __init__(self, args, debug=False):
        troi.patch.Patch.__init__(self, args, debug)

    @staticmethod
    def inputs():
        """
        Generate a top discoveries playlist for a user.

        \b
        USER_ID: is a MusicBrainz userid that has an account on ListenBrainz.
        USER_NAME: is a MusicBrainz username that has an account on ListenBrainz.
        """
        return [{"type": "argument", "args": ["user_id"]},
                {"type": "argument", "args": ["user_name"]}]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "top-discoveries-for-year"

    @staticmethod
    def description():
        return "Generate a top discoveries playlist for a user."

    def create(self, inputs):
        recs = DataSetFetcherElement(server_url="https://datasets.listenbrainz.org/top-discoveries/json",
                                     json_post_data=[{ 'user_id': inputs['user_id'] }])

        year = datetime.now().year
        pl_maker = PlaylistMakerElement(self.NAME % (year, inputs['user_name']),
                                        self.DESC % (inputs['user_name'], year),
                                        patch_slug=self.slug(),
                                        user_name=inputs['user_name'],
                                        max_artist_occurrence=2)
        pl_maker.set_sources(recs)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(pl_maker)

        return shuffle
