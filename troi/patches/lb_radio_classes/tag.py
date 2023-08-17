import troi
from random import randint

import requests

from troi import Recording
from troi.splitter import plist
from troi import TARGET_NUMBER_OF_RECORDINGS


class LBRadioTagRecordingElement(troi.Element):

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2
    MIN_RECORDINGS_EASY = NUM_RECORDINGS_TO_COLLECT
    MIN_RECORDINGS_MEDIUM = 50
    MIN_RECORDINGS_HARD = 25
    EASY_MODE_RELEASE_GROUP_MIN_TAG_COUNT = 4
    MEDIUM_MODE_ARTIST_MIN_TAG_COUNT = 4

    TAG_THRESHOLD_MAPPING = { "easy": 3, "medium": 2, "hard": 1 }

    def __init__(self, tags, operator="and", mode="easy"):
        troi.Element.__init__(self)
        self.tags = tags
        self.operator = operator
        self.mode = mode

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def fetch_tag_data(self, tags, operator, min_tag_count):
        """
            Fetch the tag data from the LB API and return it as a dict.
        """

        # Fetch our mode ranges
        start, stop = self.local_storage["modes"][self.mode]

        data = {
            "condition": operator,
            "count": self.NUM_RECORDINGS_TO_COLLECT,
            "begin_percent": start,
            "end_percent": stop,
            "tag": tags,
            "min_tag_count": min_tag_count
        }
        r = requests.get("https://api.listenbrainz.org/1/lb-radio/tags", params=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch recordings for tags. {r.text}")

        return dict(r.json())

    def collect_recordings(self, recordings, tag_data, entity, min_tag_count=None):
        """ 
            This function takes a list of recordings already collected (could be empty),
            the tag_data from the LB tag endpoint and an entity (artist, release-group, recording)
            and a minimum_tag_count that will be used to select recordings from the tag_data.

            Selected recordings will be added to the recordings and return as the first
            item in a tuple, with the second item being a boolean if the list is not full. 
            (and processing can stop).
        """

        if min_tag_count is None:
            candidates = tag_data[entity]
        else:
            candidates = []
            for rec in tag_data[entity]:
                if rec["tag_count"] >= min_tag_count:
                    candidates.append(rec)

        while len(recordings) < self.NUM_RECORDINGS_TO_COLLECT and len(candidates) > 0:
            recordings.append(candidates.pop(randint(0, len(candidates) - 1)))

        return recordings

    def get_lowest_tag_count(self, highest_tag_count):
        """ Given a highest tag count, return the lower bound for the tag_count based on how many tags exist."""

        if highest_tag_count <= 1:
            return highest_tag_count + 1  # This effectively means no tags will be collected

        if highest_tag_count <= 3:
            return highest_tag_count - 1  # use only the highest tagged recordings

        if highest_tag_count <= 5:
            return highest_tag_count - 2

        if highest_tag_count <= 8:
            return highest_tag_count - 3

        return highest_tag_count // 2

    def select_recordings_on_easy(self, recordings, tag_data, tag_count):
        try:
            highest_tag_count = tag_data["recording"][0]["tag_count"]
        except IndexError:
            highest_tag_count = 0

        if highest_tag_count > 0:
            tag_count_text = f", highest tag count for easy mode is {highest_tag_count}"
        else:
            tag_count_text = ""
        msg = f"{tag_data['count']['recording']:,} recordings tagged with '{', '.join(self.tags)}'{tag_count_text}"
        self.local_storage["user_feedback"].append(msg)

        recordings = self.collect_recordings(recordings, tag_data, "recording")
        if len(recordings) < self.MIN_RECORDINGS_EASY:
            lowest_tag_count = self.get_lowest_tag_count(highest_tag_count)
            for tag_count in range(highest_tag_count, lowest_tag_count, -1):
                recordings, canididate_count = self.collect_recordings(recordings,
                                                                       tag_data,
                                                                       "release-group",
                                                                       min_tag_count=tag_count)
                if len(recordings) >= self.NUM_RECORDINGS_TO_COLLECT:
                    break

            if len(recordings) < self.MIN_RECORDINGS_EASY:
                msg = "tag '%s' generated too few recordings for easy mode." % ", ".join(self.tags)
                recordings = self.collect_recordings(recordings, tag_data, "release-group")
                if len(recordings) >= self.MIN_RECORDINGS_MEDIUM:
                    msg += " Try medium mode instead."
                self.local_storage["user_feedback"].append(msg)

                recordings = []

        return recordings

    def select_recordings_on_medium(self, recordings, tag_data, tag_count):
        try:
            highest_tag_count = tag_data["release-group"][0]["tag_count"]
        except IndexError:
            highest_tag_count = 0

        if highest_tag_count > 0:
            tag_count_text = f", highest tag count for medium mode is {highest_tag_count}"
        else:
            tag_count_text = ""
        msg = f"At least {tag_data['count']['release-group']:,} recordings on releases and release-groups tagged with '{', '.join(self.tags)}'{tag_count_text}"

        self.local_storage["user_feedback"].append(msg)

        recordings = self.collect_recordings(recordings, tag_data, "release-group")
        if len(recordings) < self.MIN_RECORDINGS_MEDIUM:
            lowest_tag_count = self.get_lowest_tag_count(highest_tag_count)
            for tag_count in range(highest_tag_count, lowest_tag_count, -1):
                recordings = self.collect_recordings(recordings, tag_data, "artist", tag_count)
                if len(recordings) >= self.NUM_RECORDINGS_TO_COLLECT:
                    break

            if len(recordings) < self.MIN_RECORDINGS_MEDIUM:
                # Check to see if there are tagged recordings we can use
                recording_count = len(recordings)
                recordings = self.collect_recordings(recordings, tag_data, "recording")
                if len(recordings) > recording_count:
                    self.local_storage["user_feedback"].append("Stole some tagged recordings, since they were going to waste.")
                if len(recordings) < self.MIN_RECORDINGS_MEDIUM:
                    self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for medium mode." %
                                                               ", ".join(self.tags))
                    recordings = []

        return recordings

    def select_recordings_on_hard(self, recordings, tag_data, tag_count):
        try:
            highest_tag_count = tag_data["artist"][0]["tag_count"]
        except IndexError:
            highest_tag_count = 0

        if highest_tag_count > 0:
            tag_count_text = f", highest tag count for hard mode is {highest_tag_count}"
        else:
            tag_count_text = ""

        msg = f"At least {tag_data['count']['artist']:,} recordings by artists tagged with '{', '.join(self.tags)}'{tag_count_text}"
        self.local_storage["user_feedback"].append(msg)

        recordings= self.collect_recordings(recordings, tag_data, "artist")
        if len(recordings) < self.MIN_RECORDINGS_HARD:
            # Check to see if the medium mode could produce something
            recordings= self.collect_recordings(recordings, tag_data, "release-group")
            if len(recordings) >= self.MIN_RECORDINGS_MEDIUM:
                self.local_storage["user_feedback"].append(
                    "tag '%s' generated too few recordings for hard mode. Try medium mode instead." % ", ".join(self.tags))
            else:
                self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for hard mode." %
                                                           ", ".join(self.tags))
            recordings = []

        return recordings

    def read(self, entities):

        min_tag_count = self.TAG_THRESHOLD_MAPPING[self.mode]

        self.local_storage["data_cache"]["element-descriptions"].append(
            f'tag{"" if len(self.tags) == 1 else "s"} {", ".join(self.tags)}')

        tag_data = self.fetch_tag_data(self.tags, self.operator, min_tag_count)

        # Now that we've fetched the tag data, depending on mode, start collecting recordings from it. The idea
        # is to start on recordings for easy mode, release-group for medium and artist for hard mode. If not enough
        # recordings are collected, descend one level and attempt to collect more.
        recordings = plist()
        if self.mode == "easy":
            recordings = self.select_recordings_on_easy(recordings, tag_data, min_tag_count)
        elif self.mode == "medium":
            recordings = self.select_recordings_on_medium(recordings, tag_data, min_tag_count)
        else:
            recordings = self.select_recordings_on_hard(recordings, tag_data, min_tag_count)

        # Convert results into recordings
        results = []
        for rec in recordings:
            results.append(Recording(mbid=rec["recording_mbid"]))

        return results
