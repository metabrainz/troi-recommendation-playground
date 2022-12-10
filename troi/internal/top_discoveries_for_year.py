from datetime import datetime

import troi.filters
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup
import troi.sorts
from troi import Recording
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement


class TopDiscoveries(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top Discoveries of %d for %s"
    DESC = """<p>
              This playlist highlights tracks that %s first listened to in %d and listened to more than once.
              </p>
              <p>
              We generated this playlist from %s's listens and chose all the recordings
              that they first listened to this year and they listened to more than once. We removed
              recordings from duplicate artists so that ideally no artist (or an artist in a collaboration) appears
              more than twice in this playlist, although that may not always be possible. 
              Finally we randomized the order of the recordings so that two of the same artists hopefully
              won't appear in a row.
              </p>
              <p>
              Please remember that ListenBrainz may not know about all the times this user listened to a recording
              before they started sharing their listening history with us, so we apologize if recordings appear that
              this user listened to in the past. Also, we have attempted to match all of the listens to MusicBrainz
              IDs in order for them to be included in this playlist, but we may not have been able to match them all,
              so some recordings may be missing from this list.
              </p>
              <p>
              This is a review playlist that we hope will give insights into the listening habits of the year.
              </p>
           """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    def inputs():
        """
        Generate a top discoveries playlist for a user.

        \b
        USER_NAME: is a MusicBrainz username that has an account on ListenBrainz.
        """
        return [{"type": "argument", "args": ["user_name"]}]

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
        recs = DataSetFetcherElement(server_url="https://bono.metabrainz.org/top-discoveries/json",
                                     json_post_data=[{ 'user_name': inputs['user_name'] }])

        y_lookup = troi.musicbrainz.year_lookup.YearLookupElement(skip_not_found=False)
        y_lookup.set_sources(recs)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year, inputs['user_name']),
                                                      self.DESC % (inputs['user_name'], year, inputs['user_name']),
                                                      patch_slug=self.slug(),
                                                      user_name=inputs['user_name'])
        pl_maker.set_sources(y_lookup)

        shaper = PlaylistRedundancyReducerElement()
        shaper.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(shaper)

        return shuffle
