from datetime import datetime

import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist
from troi.musicbrainz.recording import RecordingListElement
from troi.playlist import PlaylistRedundancyReducerElement, PlaylistMakerElement, PlaylistShuffleElement

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
        self.recent_listens_lookup = None

    @staticmethod
    def inputs():
        """
        Generate a daily playlist from the ListenBrainz recommended recordings.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        JAM_DATE is the date for which the jam is created (this is needed to account for the fact different timezones
        can be on different dates). Recommended formatting for the date is 'YYYY-MM-DD DAY_OF_WEEK'.
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

    def apply_filters(self, user_name, element):
        deduped_raw_recs = troi.filters.DuplicateRecordingMBIDFilterElement()
        deduped_raw_recs.set_sources(element)

        raw_recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        raw_recs_lookup.set_sources(deduped_raw_recs)

        # looking up recent listens is slow so reuse this element
        # (the element caches lookup internally so reusing it avoids slow api calls)
        if self.recent_listens_lookup is None:
            self.recent_listens_lookup = troi.listenbrainz.listens.RecentListensTimestampLookup(user_name, days=2)
        self.recent_listens_lookup.set_sources(raw_recs_lookup)

        latest_filter = troi.filters.LatestListenedAtFilterElement(DAYS_OF_RECENT_LISTENS_TO_EXCLUDE)
        latest_filter.set_sources(self.recent_listens_lookup)

        feedback_lookup = troi.listenbrainz.feedback.ListensFeedbackLookup(user_name)
        feedback_lookup.set_sources(latest_filter)

        hate_filter = troi.filters.HatedRecordingsFilterElement()
        hate_filter.set_sources(feedback_lookup)

        return hate_filter

    def get_recordings(self, user_name):
        # get the list of recordings we have so far, users who regularly listen to daily jams will have
        # most of their tracks get filtered out because the recs don't change a lot on daily basis. so
        # if there is a shortfall of tracks, move on the next 100 recommendations of the user. we could
        # fetch top 200 directly in first place but then there would be an equal chance of recommending
        # someone from their 101-200 range as from 1-100. we don't want that, we want to prefer the top
        # 100 over the next 100. so only ask for more recommendations if there is a shortfall.

        # we have top 1000 recordings available in ListenBrainz. so move on to next 100 in this same manner
        # till we exhaust all recommendations available in ListenBrainz for the user or we have obtained the
        # minimum of recordings we require for daily jams.

        offset = 0
        all_recs = []
        while len(all_recs) < DAILY_JAMS_MIN_RECORDINGS and (offset + BATCH_SIZE_RECS) <= MAX_RECS_LIMIT:
            more_raw_recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(
                user_name=user_name,
                artist_type="raw",
                count=BATCH_SIZE_RECS,
                offset=offset
            )
            recordings = more_raw_recs.generate()

            element = RecordingListElement(recordings)
            filtered = self.apply_filters(user_name, element)
            recs = filtered.generate()

            all_recs.extend(recs)
            offset += BATCH_SIZE_RECS
            print()
        return RecordingListElement(all_recs)

    def create(self, inputs):
        user_name = inputs['user_name']
        jam_date = inputs.get('jam_date')
        if jam_date is None:
            jam_date = datetime.utcnow().strftime("%Y-%m-%d %a")

        recordings_element = self.get_recordings(user_name)

        pl_maker = PlaylistMakerElement(name="Daily Jams for %s, %s" % (user_name, jam_date),
                                        desc="Daily jams playlist!",
                                        patch_slug=self.slug())
        pl_maker.set_sources(recordings_element)

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        shuffle = PlaylistShuffleElement()
        shuffle.set_sources(reducer)

        return shuffle
