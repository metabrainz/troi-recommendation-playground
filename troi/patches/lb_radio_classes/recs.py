import troi
from random import randint, shuffle
from uuid import UUID

import troi
import liblistenbrainz
import liblistenbrainz.errors
from troi import Artist, Recording
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.parse_prompt import TIME_RANGES


class LBRadioRecommendationRecordingElement(troi.Element):
    """
        Given a LB user, fetch their recommended recordings and then include recordings from it.
    """

    MAX_RECOMMENDED_RECORDINGS = 1000
    MAX_RECORDINGS_TO_FETCH_PER_CALL = 100

    def __init__(self, user_name, listened="all", mode="easy"):
        troi.Element.__init__(self)
        self.user_name = user_name
        self.listened = listened
        self.mode = mode
        self.client = liblistenbrainz.ListenBrainz()

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        if self.mode == "easy":
            offset = 0
        elif self.mode == "medium":
            offset = self.MAX_RECOMMENDED_RECORDINGS // 3
        else:
            offset = self.MAX_RECOMMENDED_RECORDINGS * 2 // 3

        added = 0
        skipped = 0
        recordings = []
        count = self.MAX_RECOMMENDED_RECORDINGS // 3
        while count > 0:
            # Fetch the user recs
            try:
                result = self.client.get_user_recommendation_recordings(self.user_name, "raw",
                                                                        min(self.MAX_RECORDINGS_TO_FETCH_PER_CALL, count), offset)
            except liblistenbrainz.errors.ListenBrainzAPIException as err:
                raise RuntimeError("Cannot fetch recording stats for user %s" % self.user_name)

            if result is None or len(result['payload']['mbids']) == 0:
                break

            # Turn them into recordings
            for r in result['payload']['mbids']:
                if r['recording_mbid'] is not None:
                    offset += 1
                    latest = r.get("latest_listened_at", None)
                    if self.listened == "all" or (self.listened == "unlistened" and latest is None) or \
                            (self.listened == "listened" and latest is not None):
                        count -= 1
                        recordings.append(Recording(mbid=r['recording_mbid']))
                        added += 1
                    else:
                        skipped += 1

            # Shuffle the recordings
            shuffle(recordings)

        # Give feedback on what we collected
        listened = ""
        if self.listened != "all":
            listened = f"previously {self.listened} "

        self.local_storage["data_cache"]["element-descriptions"].append(f"{self.user_name}'s {listened}recommended songs")

        # TODO: How do we prevent sequential tracks by the same artist?

        return recordings
