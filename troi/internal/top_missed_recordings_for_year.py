from datetime import datetime

import troi
from troi import Recording
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement


class TopMissedTracksPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top Missed Recordings of %d for %s"
    DESC = """<p>
              This playlist is made from recordings that %s's most similar users listened to this year, but that
              %s didn't listen to this year.
              </p>
              <p>
              We determined the top 3 most similar users to %s and selected all of the recordings
              they listened to this year. We then removed all of the recordings that %s listened to from
              this list of recordings, leaving only those that they didn't listen to. We removed recordings from
              duplicate artists so that ideally no artist (or an artist in a collaboration) appears
              more than twice in this playlist, although that may not always be possible. Finally we
              randomized the order of the recordings so that two of the same artists hopefully won't appear
              in a row.
              </p>
              <p>
              We have attempted to match all of the listens to MusicBrainz
              IDs in order for them to be included in this playlist, but we may not have been able to match them all,
              so some recordings may be missing from this list.
              </p>
              <p>
              This is a discovery playlist that will hopefully introduce the user to some new recordings
              that other similar users love. Because this is a discovery playlist, it may require
              more active listening since it may contain tracks that are not fully to the taste of the user.
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        """
        Generate a top missed tracks playlists for a given user.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        """
        return [
            {
                "type": "argument",
                "args": ["user_name"],
                "kwargs": {}
            }
        ]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "top-missed-recordings-for-year"

    @staticmethod
    def description():
        return "Generate a playlist from the top tracks that the most similar users listened to, but the user didn't listen to."

    def create(self, inputs):
        source = DataSetFetcherElement(server_url="https://bono.metabrainz.org/top-missed-tracks/json",
                                       json_post_data=[{ 'user_name': inputs['user_name'] }])

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year, inputs['user_name']),
                                                      self.DESC % (inputs['user_name'], inputs['user_name'], inputs['user_name'], inputs['user_name']),
                                                      patch_slug=self.slug(),
                                                      user_name=inputs['user_name'])
        pl_maker.set_sources(source)

        reducer = PlaylistRedundancyReducerElement(max_num_recordings=self.max_num_recordings)
        reducer.set_sources(pl_maker)

        return reducer
