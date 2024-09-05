import troi
from time import sleep
from random import shuffle

import requests

from troi import Recording
from troi import TARGET_NUMBER_OF_RECORDINGS


class LBRadioPlaylistRecordingElement(troi.Element):
    """
        Given an LB playlist, fetch its tracks and randomly include recordiungs from it. mode does not
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

        # Fetch the playlist
        while True:
            r = requests.get(f"https://api.listenbrainz.org/1/playlist/{self.mbid}")
            if r.status_code == 404:
                raise RuntimeError(f"Cannot find playlist {self.mbid}.")
            if r.status_code == 429:
                sleep(2)
                continue
            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch playlist {self.mbid}. {r.text}")

            break

        # Give feedback about the playlist
        self.local_storage["data_cache"]["element-descriptions"].append(f"playlist {self.mbid}")

        # Fetch the recordings, then shuffle
        mbid_list = []
        for recording in r.json()["playlist"]["track"]:
            identifiers = recording["identifier"]
            if isinstance(identifiers, str):
                identifiers = [identifiers]

            mbid = None
            for identifier in identifiers:
                if identifier.startswith("https://musicbrainz.org/recording/") or \
                        identifier.startswith("http://musicbrainz.org/recording/"):
                    mbid = identifier.split("/")[-1]
                    break

            mbid_list.append(mbid)

        shuffle(mbid_list)

        # Select and convert the first n MBIDs into Recordings
        recordings = []
        for mbid in mbid_list[:self.NUM_RECORDINGS_TO_COLLECT]:
            recordings.append(Recording(mbid=mbid))

        return recordings
