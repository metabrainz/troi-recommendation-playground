from random import shuffle
from time import sleep

import requests

import troi
from troi import Recording
from troi import TARGET_NUMBER_OF_RECORDINGS


class LBRadioCollectionRecordingElement(troi.Element):
    """
        Given an MB recording collection, fetch it and randomly include recordings from it. mode does not
        apply to this element.
    """

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2

    def __init__(self, mbid, mode="easy"):
        troi.Element.__init__(self)
        self.mbid = mbid
        self.mode = mode

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        # Fetch collection recordings
        params = {"collection": self.mbid, "fmt": "json"}

        while True:
            r = requests.get("https://musicbrainz.org/ws/2/recording", params=params)
            if r.status_code == 404:
                raise RuntimeError(f"Cannot find collection {self.mbid}.")

            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch collection {self.mbid}. {r.text}")

            break

        # Give feedback about what we collected
        self.local_storage["data_cache"]["element-descriptions"].append(f"collection {self.mbid}")

        # Fetch the recordings, then shuffle
        mbid_list = []
        for r in r.json()["recordings"]:
            if not r["video"]:
                mbid_list.append(r["id"])
        shuffle(mbid_list)

        # Select and convert the first n MBIDs into Recordings
        recordings = []
        for mbid in mbid_list[:self.NUM_RECORDINGS_TO_COLLECT]:
            recordings.append(Recording(mbid=mbid))

        return recordings
