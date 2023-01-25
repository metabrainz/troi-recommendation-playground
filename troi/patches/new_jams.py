from datetime import datetime

import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist, Element, Recording
from troi.musicbrainz.recording import RecordingListElement
from troi.playlist import PlaylistMakerElement, PlaylistShuffleElement

DAYS_OF_RECENT_LISTENS_TO_EXCLUDE = 60  # Exclude tracks listened in last X days from the daily jams playlist
DAILY_JAMS_MIN_RECORDINGS = 25  # the minimum number of recordings we aspire to have in a daily jam, this is not a hard limit
BATCH_SIZE_RECS = 100  # the number of recommendations fetched in 1 go
MAX_RECS_LIMIT = 1000  # the maximum of recommendations available in LB


class NewJamsPatch(troi.patch.Patch):
    """
    """

    def __init__(self, debug=False):
        super().__init__(debug)

    @staticmethod
    def inputs():
        """
        Generate a playlist from the ListenBrainz recommended recordings that the user has not listened to.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        """
        return [
            {"type": "argument", "args": ["user_name"]}
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "new-jams"

    @staticmethod
    def description():
        return "Generate a playlist from the ListenBrainz recommended recordings that the user has not listened to."

    def create(self, inputs):
        user_name = inputs['user_name']

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name, "raw", count=1000)

        recent_listens_lookup = troi.listenbrainz.listens.RecentListensTimestampLookup(user_name, days=2)
        recent_listens_lookup.set_sources(recs)

        # Remove tracks that have been listened to before.
        never_listened = troi.filters.NeverListenedFilterElement(remove_unlistened=False)
        never_listened.set_sources(recent_listens_lookup)

        feedback_lookup = troi.listenbrainz.feedback.ListensFeedbackLookup(user_name)
        feedback_lookup.set_sources(never_listened)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(feedback_lookup)

        # You'd think you wouldn't need a hate filter for tracks a user has never listened to,
        # but there are users who fake listens just to hate them. Commenting for a friend.
        hate_filter = troi.filters.HatedRecordingsFilterElement()
        hate_filter.set_sources(recs_lookup)

        pl_maker = PlaylistMakerElement(name="New Jams for %s" % (user_name),
                                        desc="This playlist contains tracks that you have not listened to yet.",
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=2)
        pl_maker.set_sources(hate_filter)

        return pl_maker
