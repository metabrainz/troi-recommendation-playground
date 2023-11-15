import troi
from collections import defaultdict
from random import randint, shuffle

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

        if self.mode == "easy":
            start, stop = 0, 50
        elif self.mode == "medium":
            start, stop = 25, 75
        else:
            start, stop = 50, 100

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


    def fetch_similar_recordings(self, recording_mbids):

        SIMILARITY_ALGORITHM = "session_based_days_9000_session_300_contribution_5_threshold_15_limit_50_skip_30"
        
        mbids = [ { "recording_mbid": rec, "algorithm": SIMILARITY_ALGORITHM } for rec in recording_mbids ]
        r = requests.post("https://labs.api.listenbrainz.org/similar-recordings/json", json=mbids)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch similar recordings: {r.status_code} ({r.text})")

        try:
            recordings = r.json()[3]["data"]
        except IndexError:
            return []

        index = defaultdict(plist)
        for rec in recordings:
            index[rec["reference_mbid"]].append(rec["recording_mbid"])

        # How random the similar tracks are, happens in this loop. Tune this first.
        result = []
        for k in index:
            result.append({ rec["reference_mbid"]: index[k].random_item(0, 100) })

        print(f"in {len(recording_mbids)} out: {len(result)}")

        return result


    def fuzz_up_boring_tag_data(self, tag_data):

        # Combine all the tag data into one array
        tag_recording_mbids = plist(tag_data["recording"])
        tag_recording_mbids.extend(tag_data["release-group"])
        tag_recording_mbids.extend(tag_data["artist"])
        tag_recording_mbids = plist([ t["recording_mbid"] for t in tag_recording_mbids ])
    
        if self.mode == "medium":
            start, stop = 33, 66
            max_num_similar_tracks = TARGET_NUMBER_OF_RECORDINGS
        else:
            start, stop = 66, 100
            max_num_similar_tracks = TARGET_NUMBER_OF_RECORDINGS * 2

        # Now randomly select our minimum of tracks
        recordings = plist()
        for recording in tag_recording_mbids.random_item(start, stop, self.NUM_RECORDINGS_TO_COLLECT):
            recordings.append(recording)

        similar_recordings_index = self.fetch_similar_recordings(recordings)
        similar_recordings = []
        for recording in recordings:
            if recording in similar_recordings_index:
                similar_recordings.append(similar_recordings_index[recording])
                del tag_recording_mbids[recording]

        similar_recordings.extend(recordings.random_item(start, stop, self.NUM_RECORDINGS_TO_COLLECT - len(similar_recordings))) 
        shuffle(similar_recordings) 

        return similar_recordings

    def read(self, entities):

        # TODO: Should this be set lower for harder modes and loads of tags? We need to wait for more user feedback on this.
        threshold = 1

        self.local_storage["data_cache"]["element-descriptions"].append(
            f'tag{"" if len(self.tags) == 1 else "s"} {", ".join(self.tags)}')

        tag_data = self.fetch_tag_data(self.tags, self.operator, threshold)
        recordings = self.fuzz_up_boring_tag_data(tag_data)
        # Convert results into recordings
        results = []
        for rec in recordings:
            results.append(Recording(mbid=rec))

        return results
