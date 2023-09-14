import troi
from random import randint

import requests

from troi import Recording
from troi.splitter import plist
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.utils import interleave


class LBRadioTagRecordingElement(troi.Element):

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2
    MIN_RECORDINGS_EASY = NUM_RECORDINGS_TO_COLLECT
    MIN_RECORDINGS_MEDIUM = 50
    MIN_RECORDINGS_HARD = 25
    EASY_MODE_RELEASE_GROUP_MIN_TAG_COUNT = 4
    MEDIUM_MODE_ARTIST_MIN_TAG_COUNT = 4

    TAG_THRESHOLD_MAPPING = {"easy": 3, "medium": 2, "hard": 1}

    def __init__(self, tags, operator="and", mode="easy", include_similar_tags=True):
        troi.Element.__init__(self)
        self.tags = tags
        self.operator = operator
        self.mode = mode
        self.include_similar_tags = include_similar_tags

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

    def fetch_similar_tags(self, tag):
        """
            Fetch similar tags from LB
        """

        r = requests.post("https://datasets.listenbrainz.org/tag-similarity/json", json=[{"tag": tag}])
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch similar tags. {r.text}")

        return plist(r.json())

    def flatten_tag_data(self, tag_data):

        flat_data = list(tag_data["recording"])
        flat_data.extend(list(tag_data["release-group"]))
        flat_data.extend(list(tag_data["artist"]))

        return plist(sorted(flat_data, key=lambda f: f["percent"], reverse=True))

    def select_recordings_on_easy(self, tag_data):

        msgs = [ ]
        start, stop = self.local_storage["modes"]["easy"]

        msgs = [f"""tag: using seed tags: '{ "', '".join(self.tags)}' only"""]
        return tag_data.random_item(start, stop, self.NUM_RECORDINGS_TO_COLLECT), msgs

    def select_recordings_on_medium(self, tag_data):

        msgs = [ ]
        start, stop = self.local_storage["modes"]["medium"]
        result = tag_data.random_item(start, stop, self.NUM_RECORDINGS_TO_COLLECT)

        if len(self.tags) == 1 and self.include_similar_tags:
            similar_tags = self.fetch_similar_tags(self.tags[0])
            similar_tag = similar_tags.random_item(0, 50, 1)
            if similar_tag is not None:
                similar_tag = similar_tag["similar_tag"]
                msgs = [f"tag: using seed tag '{self.tags[0]}' and similar tag '{similar_tag}'."]

                sim_tag_data = self.fetch_tag_data([similar_tag], "OR", 1)
                sim_tag_data = self.flatten_tag_data(sim_tag_data)

                return interleave((result, sim_tag_data)), msgs

        msgs = [f"""tag: using seed tags: '{ "', '".join(self.tags)}' only"""]
        return result, msgs

    def select_recordings_on_hard(self, tag_data):

        msgs = [ ]
        start, stop = self.local_storage["modes"]["hard"]
        result = tag_data.random_item(start, stop, self.NUM_RECORDINGS_TO_COLLECT)

        start, stop = 10, 50 
        if len(self.tags) == 1 and self.include_similar_tags:
            similar_tags = self.fetch_similar_tags(self.tags[0])
            if len(similar_tags[start:stop]) > 2:
                while True:
                    selected_tags = similar_tags.random_item(10, 50, 2)
                    if selected_tags[0] == selected_tags[1]:
                        print("same tag selected!")
                        continue

                    break
                similar_tags = selected_tags
            else:
                similar_tags = similar_tags[start:stop]

            similar_tags = [ tag["similar_tag"] for tag in similar_tags ]

            if len(similar_tags) > 0:
                sim_tag_data = self.fetch_tag_data((self.tags[0], similar_tags[0]), "AND", 1)
                sim_tag_data = self.flatten_tag_data(sim_tag_data)
            
                if len(similar_tags) > 1:
                    sim_tag_data_2 = self.fetch_tag_data((self.tags[0], similar_tags[1]), "AND", 1)
                    sim_tag_data_2 = self.flatten_tag_data(sim_tag_data_2)
                    msgs = [f"""tag: using seed tag '{self.tags[0]}' and similar tags '{"', '".join(similar_tags)}'."""]
                else:
                    msgs = [f"""tag: using seed tag '{self.tags[0]}' and similar tag '{similar_tags[0]}'."""]
                    sim_tag_data_2 = []

                return interleave((result, sim_tag_data, sim_tag_data_2)), msgs
        else:
            msgs = [f"""tag: using only seed tag '{self.tags[0]}'."""]

        return result, msgs

    def read(self, entities):

        min_tag_count = self.TAG_THRESHOLD_MAPPING[self.mode]

        self.local_storage["data_cache"]["element-descriptions"].append(
            f'tag{"" if len(self.tags) == 1 else "s"} {", ".join(self.tags)}')

        tag_data = self.fetch_tag_data(self.tags, self.operator, min_tag_count)
        tag_data = self.flatten_tag_data(tag_data)

        recordings = plist()
        if self.mode == "easy":
            recordings, feedback = self.select_recordings_on_easy(tag_data)
        elif self.mode == "medium":
            recordings, feedback = self.select_recordings_on_medium(tag_data)
        else:
            recordings, feedback = self.select_recordings_on_hard(tag_data)

        for msg in feedback:
            self.local_storage["user_feedback"].append(msg)

        # Convert results into recordings
        results = []
        for rec in recordings:
            results.append(Recording(mbid=rec["recording_mbid"]))

        return results
