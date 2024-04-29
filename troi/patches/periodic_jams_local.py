from datetime import datetime, timedelta

import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist
from troi.patch import Patch
from troi.playlist import PlaylistMakerElement

from troi.local.recording_resolver import RecordingResolverElement

DAYS_OF_RECENT_LISTENS_TO_EXCLUDE = 60  # Exclude tracks listened in last X days from the daily jams playlist
DAILY_JAMS_MIN_RECORDINGS = 25  # the minimum number of recordings we aspire to have in a daily jam, this is not a hard limit
BATCH_SIZE_RECS = 1000  # the number of recommendations fetched in 1 go
MAX_RECS_LIMIT = 1000  # the maximum of recommendations available in LB


class PeriodicJamsLocalPatch(Patch):
    """
    """

    def __init__(self, args):
        super().__init__(args)

    @staticmethod
    def inputs():
        """
        Generate a periodic playlist from the ListenBrainz recommended recordings.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        """
        return [{
            "type": "argument",
            "args": ["user_name"]
        }]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "periodic-jams-local"

    @staticmethod
    def description():
        return "Generate a localized periodic playlist from the ListenBrainz recommended recordings."

    def is_local(self):
        return True

    def create(self, inputs):
        user_name = inputs['user_name']

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name,
                                                                          "raw",
                                                                          count=1000)

        recent_listens_lookup = troi.listenbrainz.listens.RecentListensTimestampLookup(user_name,
                                                                                       days=2)
        recent_listens_lookup.set_sources(recs)

        latest_filter = troi.filters.LatestListenedAtFilterElement(DAYS_OF_RECENT_LISTENS_TO_EXCLUDE)
        latest_filter.set_sources(recent_listens_lookup)

        feedback_lookup = troi.listenbrainz.feedback.ListensFeedbackLookup(user_name, auth_token=inputs.get("token"))
        feedback_lookup.set_sources(latest_filter)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(feedback_lookup)

        resolve = RecordingResolverElement(.8, self.quiet)
        resolve.set_sources(recs_lookup)

        pl_maker = PlaylistMakerElement(name="Weekly Jams for %s" % (user_name),
                                        desc="test playlist!",
                                        patch_slug="periodic-jams",
                                        max_num_recordings=50,
                                        max_artist_occurrence=2,
                                        shuffle=True,
                                        expires_at=datetime.utcnow() + timedelta(weeks=2))
        pl_maker.set_sources(resolve)

        return pl_maker
