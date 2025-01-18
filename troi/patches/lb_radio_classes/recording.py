from time import sleep

import troi
from random import randint, shuffle

import requests

from troi import Recording
from troi.plist import plist
from troi import TARGET_NUMBER_OF_RECORDINGS


class LBRadioRecordRecordingElement(troi.Element):
    """
    Given a MBID for a record, fetch similar recordings and then include recordings from it.
    """

    MAX_RECOMMENDED_RECORDINGS = 0

    def __init__(self, mbid, mode="easy"):
        troi.Element.__init__(self)
        self.mbid = [mbid]
        self.mode = mode
        self.algorithm = "session_based_days_9000_session_300_contribution_5_threshold_15_limit_50_skip_30"

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def fetch_similar_recordings(self, mbid, algorithm):
        """
        Fetch similar recordings from LB
        """

        while True:
            r = requests.post(
                "https://labs.api.listenbrainz.org/similar-recordings/json",
                json=[{"recording_mbids": mbid, "algorithm": algorithm}],
            )
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code == 404:
                return plist()

            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch similar recordings. {r.text}")

            break

        self.MAX_RECOMMENDED_RECORDINGS = len(r.json())
        return plist(r.json())

    def read(self, entities):

        recordings = []
        result = self.fetch_similar_recordings(self.mbid, self.algorithm)
        if self.mode == "easy":
            count = self.MAX_RECOMMENDED_RECORDINGS // 3
        elif self.mode == "medium":
            count = self.MAX_RECOMMENDED_RECORDINGS * 2 // 3
        else:
            count = self.MAX_RECOMMENDED_RECORDINGS

        for i in range(0, count):
            recordings.append(Recording(mbid=result[i]["recording_mbid"]))

        self.local_storage["data_cache"]["element-descriptions"].append(
            f"{self.mbid}'s {len(recordings)} similar recordings"
        )
        return recordings
