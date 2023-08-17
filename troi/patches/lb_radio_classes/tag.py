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

    def __init__(self, tags, operator="and", mode="easy"):
        troi.Element.__init__(self)
        self.tags = tags
        self.operator = operator
        self.mode = mode

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def fetch_tag_data(self, tags, operator, threshold):
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
            "threshold": threshold
        }
        r = requests.get("https://api.listenbrainz.org/1/lb-radio/tags", params=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch recordings for tags. {r.text}")

        return dict(r.json())

    def collect_recordings(self, recordings, tag_data, entity, min_tag_count=None, quiet=False):
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

        tagged_with = f"tagged with '{', '.join(self.tags)}'"
        if len(tag_data[entity]) > 0:
            tag_count = f", highest tag count {tag_data[entity][0]['tag_count']}"
        else:
            tag_count = ""

        if entity == "artist":
            if min_tag_count is None:
                msg = f"{tag_data['count']['artist']:,} recordings by artists {tagged_with}{tag_count}"
            else:
                msg = f"{len(candidates):,} recordings by artists {tagged_with} at least {min_tag_count} times{tag_count}"
        elif entity == "release-group":
            if min_tag_count is None:
                msg = f"{tag_data['count']['release-group']:,} recordings on releases and release-groups {tagged_with}{tag_count}"
            else:
                msg = f"{len(candidates):,} recordings on releases and release-groups {tagged_with} at least {min_tag_count} times{tag_count}"
        else:
            if min_tag_count is None:
                msg = f"{tag_data['count']['recording']:,} recordings {tagged_with}{tag_count}"
            else:
                msg = f"{len(candidates):,} recordings {tagged_with} at least {min_tag_count} times, {tag_count}"

        if not quiet:
            self.local_storage["user_feedback"].append(msg)

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

    def read(self, entities):

        # TODO: Should this be set lower for harder modes and loads of tags? We need to wait for more user feedback on this.
        threshold = 1

        self.local_storage["data_cache"]["element-descriptions"].append(
            f'tag{"" if len(self.tags) == 1 else "s"} {", ".join(self.tags)}')

        tag_data = self.fetch_tag_data(self.tags, self.operator, threshold)

        # Now that we've fetched the tag data, depending on mode, start collecting recordings from it. The idea
        # is to start on recordings for easy mode, release-group for medium and artist for hard mode. If not enough
        # recordings are collected, descend one level and attempt to collect more.
        recordings = plist()
        if self.mode == "easy":
            recordings = self.collect_recordings(recordings, tag_data, "recording", min_tag_count=None)
            if len(recordings) < self.MIN_RECORDINGS_EASY:
                try:
                    highest_tag_count = tag_data["recording"][0]["tag_count"]
                except IndexError:
                    highest_tag_count = 0
                lowest_tag_count = self.get_lowest_tag_count(highest_tag_count)
                for tag_count in range(highest_tag_count, lowest_tag_count, -1):
                    recordings = self.collect_recordings(recordings, tag_data, "release-group", min_tag_count=tag_count)
                    if len(recordings) >= self.NUM_RECORDINGS_TO_COLLECT:
                        break

                if len(recordings) < self.MIN_RECORDINGS_EASY:
                    self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for easy mode." %
                                                               ", ".join(self.tags))
                    if len(recordings) >= self.MIN_RECORDINGS_MEDIUM:
                        self.local_storage["user_feedback"].append("There are enough tags for medium mode, try it!")
                    recordings = []

        elif self.mode == "medium":
            recordings = self.collect_recordings(recordings, tag_data, "release-group", min_tag_count=None)
            if len(recordings) < self.MIN_RECORDINGS_MEDIUM:
                try:
                    highest_tag_count = tag_data["release-group"][0]["tag_count"]
                except IndexError:
                    highest_tag_count = 0
                lowest_tag_count = self.get_lowest_tag_count(highest_tag_count)
                for tag_count in range(highest_tag_count, lowest_tag_count, -1):
                    recordings = self.collect_recordings(recordings, tag_data, "artist", min_tag_count=tag_count)
                    if len(recordings) >= self.NUM_RECORDINGS_TO_COLLECT:
                        break

                if len(recordings) < self.MIN_RECORDINGS_MEDIUM:
                    # Check to see if there are tagged recordings we can use
                    recording_count = len(recordings)
                    recordings = self.collect_recordings(recordings, tag_data, "recording", min_tag_count=None)
                    if len(recordings) > recording_count:
                        self.local_storage["user_feedback"].append("Stole some tagged recordings, since they were going to waste.")
                    if len(recordings) < self.MIN_RECORDINGS_MEDIUM:
                        self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for medium mode." %
                                                                   ", ".join(self.tags))
                        recordings = []
        else:
            recordings = self.collect_recordings(recordings, tag_data, "artist", min_tag_count=None)
            if len(recordings) < self.MIN_RECORDINGS_HARD:
                self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for hard mode." %
                                                           ", ".join(self.tags))
                recordings = []

        # Convert results into recordings
        results = []
        for rec in recordings:
            results.append(Recording(mbid=rec["recording_mbid"]))

        return results
