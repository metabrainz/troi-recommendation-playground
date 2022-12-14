from datetime import datetime

import troi.filters
import troi.listenbrainz.stats
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup
import troi.sorts
from troi import Recording
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement


class TopTracksYouListenedToPatch(troi.patch.Patch):
    """
        See below for description
    """
    NAME = "Top New Releases in %d for %s"
    DESC = """<p>
              This playlist highlights recordings released in %d that %s listened to the most.
              </p>
              <p>
              We generated this playlist from the user's listens and chose all the recordings
              that were released this year and that the user listened to often. We removed recordings
              from duplicate artists so that ideally no artist (or an artist in a collaboration) appears
              more than twice in this playlist, although that may not always be possible. Finally we randomized
              the order of the recordings so that two of the same artists hopefully won't appear in a row.
              </p>
              <p>
              We have attempted to match all of the listens to MusicBrainz
              IDs in order for them to be included in this playlist, but we may not have been able to match them all,
              so some recordings may be missing from this list.
              </p>
              <p>
              This is a review playlist that we hope will give insights the music released during the year.
              </p>"""

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        """
        Generate a playlist that contains a mix of tracks released this year that you've
        listened to.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        """
        return [{"type": "argument", "args": ["user_name"]}]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "top-new-recordings-for-year"

    @staticmethod
    def description():
        return "Generate a playlist of tracks released this year that you've listened to."

    def create(self, inputs):
        recs = DataSetFetcherElement(server_url="https://datasets.listenbrainz.org/top-new-tracks/json",
                                     json_post_data=[{ 'user_name': inputs['user_name'] }])

        y_lookup = troi.musicbrainz.year_lookup.YearLookupElement(skip_not_found=False)
        y_lookup.set_sources(recs)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year, inputs['user_name']),
                                                      self.DESC % (year, inputs['user_name']),
                                                      patch_slug=self.slug(),
                                                      user_name=inputs['user_name'])
        pl_maker.set_sources(recs)

        shaper = PlaylistRedundancyReducerElement()
        shaper.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(shaper)

        return shuffle
