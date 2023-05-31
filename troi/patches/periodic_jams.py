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


class PeriodicJamsPatch(troi.patch.Patch):
    """
       Create either daily-jams, weekly-jams or weekly-new-jams with this patch.

       First, fetch the top recommendations. For daily-jams and weekly-jams, filter out the recently listened tracks.
       For weekly-new-jams, filter out tracks that have been listened to.

       Then filter out hated tracks and make the playlist.
    """

    JAM_TYPES = ("daily-jams", "weekly-jams", "weekly-new-jams")

    def __init__(self, debug=False):
        super().__init__(debug)

    @staticmethod
    def inputs():
        """
        Generate a periodic playlist from the ListenBrainz recommended recordings.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        TYPE Must be one of "daily-jams", "weekly-jams" or "weekly-new-jams".
        JAM_DATE is the date for which the jam is created (this is needed to account for the fact different timezones
        can be on different dates). Required formatting for the date is 'YYYY-MM-DD'.
        """
        return [
            {"type": "argument", "args": ["user_name"]},
            {"type": "argument", "args": ["type"], "kwargs": {"required": False}},
            {"type": "argument", "args": ["jam_date"], "kwargs": {"required": False}}
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "periodic-jams"

    @staticmethod
    def description():
        return "Generate a periodic playlist from the ListenBrainz recommended recordings."

    def create(self, inputs):
        user_name = inputs['user_name']
        jam_date = inputs.get('jam_date')
        if jam_date is None:
            jam_date = datetime.utcnow().strftime("%Y-%m-%d %a")
        jam_type = inputs.get('type')
        if jam_type is None:
            jam_type = self.JAM_TYPES[0]
        else:
            jam_types = jam_type.lower()
            if jam_type not in self.JAM_TYPES:
                raise RuntimeError("Jam type must be one of %s" % ", ".join(jam_types))

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name, "raw", count=1000, auth_token=inputs.get("token"))

        recent_listens_lookup = troi.listenbrainz.listens.RecentListensTimestampLookup(user_name, days=2, auth_token=inputs.get("token"))
        recent_listens_lookup.set_sources(recs)

        if jam_type in ("daily-jams", "weekly-jams"):
            # Remove tracks that have not been listened to before.
            never_listened = troi.filters.NeverListenedFilterElement()
            never_listened.set_sources(recent_listens_lookup)
            if jam_type == "daily-jams":
                jam_name = "Daily Jams"
            else:
                jam_name = "Weekly Jams"
                jam_date = "week of " + jam_date
        elif jam_type == "weekly-new-jams":
            # Remove tracks that have been listened to before.
            never_listened = troi.filters.NeverListenedFilterElement(remove_unlistened=False)
            never_listened.set_sources(recent_listens_lookup)
            jam_name = "Weekly New Jams"
            jam_date = "week of " + jam_date
        else:
            raise RuntimeError("someone goofed up!")

        latest_filter = troi.filters.LatestListenedAtFilterElement(DAYS_OF_RECENT_LISTENS_TO_EXCLUDE)
        latest_filter.set_sources(never_listened)

        feedback_lookup = troi.listenbrainz.feedback.ListensFeedbackLookup(user_name, auth_token=inputs.get("token"))
        feedback_lookup.set_sources(latest_filter)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(feedback_lookup)

        hate_filter = troi.filters.HatedRecordingsFilterElement()
        hate_filter.set_sources(recs_lookup)

        pl_maker = PlaylistMakerElement(name="%s for %s, %s" % (jam_name, user_name, jam_date),
                                        desc="%s playlist!" % jam_name,
                                        patch_slug=jam_type,
                                        max_num_recordings=50,
                                        max_artist_occurrence=2,
                                        shuffle=True,
                                        is_april_first=(jam_date[5:10] == "04-01"))
        pl_maker.set_sources(hate_filter)

        return pl_maker
