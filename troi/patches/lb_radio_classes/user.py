import troi
from random import randint, shuffle
from uuid import UUID

import troi
import pylistenbrainz
import pylistenbrainz.errors
from troi import Recording
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.parse_prompt import TIME_RANGES


class LBRadioUserRecordingElement(troi.Element):
    """
        Given a LB user, fetch their recording stats and then include recordings from it.
    """

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2

    def __init__(self, user_name, time_range, mode="easy"):
        troi.Element.__init__(self)
        self.user_name = user_name
        self.time_range = time_range
        self.mode = mode
        self.client = pylistenbrainz.ListenBrainz()

        if time_range not in TIME_RANGES:
            raise RuntimeError("entity user must specify one of the following time range options: " + ", ".join(TIME_RANGES))

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        if self.mode == "easy":
            offset = 0
        elif self.mode == "medium":
            offset = 100
        else:
            offset = 200

        try:
            result = self.client.get_user_recordings(self.user_name, 100, offset, self.time_range)
        except pylistenbrainz.errors.ListenBrainzAPIException as err:
            raise RuntimeError("Cannot fetch recording stats for user %s" % self.user_name)

        self.local_storage["data_cache"]["element-descriptions"].append(f"user {self.user_name} stats for {self.time_range}")

        recordings = []
        for r in result['payload']['recordings']:
            if r['recording_mbid'] is not None:
                recordings.append(Recording(mbid=r['recording_mbid']))

        shuffle(recordings)

        return recordings
