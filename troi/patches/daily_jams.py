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


class DailyJamsPatch(troi.patch.Patch):
    """
        Taken a list of Recordings, break them into 7 roughly equal chunks and return
        the chunk for the given day of the week.
    """

    def __init__(self, debug=False):
        super().__init__(debug)

    @staticmethod
    def inputs():
        """
        Generate a daily playlist from the ListenBrainz recommended recordings.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        JAM_DATE is the date for which the jam is created (this is needed to account for the fact different timezones
        can be on different dates). Required formatting for the date is 'YYYY-MM-DD'.
        """
        return [
            {"type": "argument", "args": ["user_name"]},
            {"type": "argument", "args": ["jam_date"], "kwargs": {"required": False}}
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "daily-jams"

    @staticmethod
    def description():
        return "Generate a daily playlist from the ListenBrainz recommended recordings."

    def create(self, inputs):
        user_name = inputs['user_name']
        jam_date = inputs.get('jam_date')
        if jam_date is None:
            jam_date_dt  = datetime.utcnow()
        else:
            try:
                jam_date_dt = datetime.strptime(jam_date, "%Y-%m-%d")
            except ValueError:
                raise RuntimeError(f"Cannot parse date {jam_date}. Must be in format YYYY-MM-DD.")

        jam_date = jam_date_dt.strftime("%Y-%m-%d %a")

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name, "raw", count=1000)

        recent_listens_lookup = troi.listenbrainz.listens.RecentListensTimestampLookup(user_name, days=2)
        recent_listens_lookup.set_sources(recs)

        # Remove tracks that have not been listened to before.
        never_listened = troi.filters.NeverListenedFilterElement()
        never_listened.set_sources(recent_listens_lookup)

        latest_filter = troi.filters.LatestListenedAtFilterElement(DAYS_OF_RECENT_LISTENS_TO_EXCLUDE)
        latest_filter.set_sources(never_listened)

        feedback_lookup = troi.listenbrainz.feedback.ListensFeedbackLookup(user_name)
        feedback_lookup.set_sources(latest_filter)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(feedback_lookup)

        hate_filter = troi.filters.HatedRecordingsFilterElement()
        hate_filter.set_sources(recs_lookup)

        pl_maker = PlaylistMakerElement(name="Daily Jams for %s, %s" % (user_name, jam_date),
                                        desc="Daily jams playlist!",
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=2,
                                        shuffle=True)
        pl_maker.set_sources(hate_filter)

        return pl_maker
