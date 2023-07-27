import troi
from random import randint, shuffle
from uuid import UUID

import troi
import pylistenbrainz
import pylistenbrainz.errors
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
        self.client = pylistenbrainz.ListenBrainz()

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

        recordings = []
        count = self.MAX_RECOMMENDED_RECORDINGS // 3
        while count > 0:
            # Fetch the user recs
            try:
                result = self.client.get_user_recommendation_recordings(self.user_name, "raw",
                                                                        min(self.MAX_RECORDINGS_TO_FETCH_PER_CALL, count), offset)
            except pylistenbrainz.errors.ListenBrainzAPIException as err:
                raise RuntimeError("Cannot fetch recording stats for user %s" % self.user_name)

            # Give feedback on what we collected
            self.local_storage["data_cache"]["element-descriptions"].append(f"{self.user_name}'s recommended songs")

            # Turn them into recordings
            for r in result['payload']['mbids']:
                if r['recording_mbid'] is not None:
                    count -= 1
                    offset += 1
                    recordings.append(Recording(mbid=r['recording_mbid']))

            # Shuffle the recordings
            shuffle(recordings)

        # How do we prevent sequential tracks by the same artist?

        return recordings
