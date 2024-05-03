from time import sleep

import troi
from random import randint, shuffle

import requests

from troi import Recording
from troi.plist import plist
from troi import TARGET_NUMBER_OF_RECORDINGS


class LBRadioTagRecordingElement(troi.Element):

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 4

    def __init__(self,
                 tags,
                 operator="and",
                 mode="easy",
                 include_similar_tags=True):
        troi.Element.__init__(self)
        self.tags = tags
        self.operator = operator
        self.mode = mode
        self.include_similar_tags = include_similar_tags

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def fetch_similar_tags(self, tag):
        """
            Fetch similar tags from LB
        """

        while True:
            r = requests.post("https://labs.api.listenbrainz.org/tag-similarity/json", json=[{"tag": tag}])
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code == 404:
                return plist()

            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch similar tags. {r.text}")

            break

        return plist(r.json())

    def select_recordings(self):

        msgs = []
        start, stop = { "easy": (66, 95), "medium": (33, 66), "hard": (1, 33) }[self.mode]
        sim_start, sim_stop = { "easy": (0, 0), "medium": (50, 100), "hard": (10, 50) }[self.mode]
        num_similar_tags_to_include = { "easy": 0, "medium": 1, "hard": 2 }[self.mode] 

        recordings = self.recording_search_by_tag.search(self.tags, self.operator, start, stop,
                                                         self.NUM_RECORDINGS_TO_COLLECT)
        if not recordings:
            return [], ["Could not find any recordings for tag search '%s', ignoring." % (",".join(self.tags)) ] 

        if len(self.tags) == 1 and self.include_similar_tags:
            similar_tags = self.fetch_similar_tags(self.tags[0])

            if len(similar_tags[sim_start:sim_stop]) > 2:
                while True:
                    selected_tags = similar_tags.random_item(count=2)
                    if selected_tags[0] == selected_tags[1]:
                        continue

                    break
                similar_tags = selected_tags
            else:
                similar_tags = similar_tags[sim_start:sim_stop]

            similar_tags = [tag["similar_tag"] for tag in similar_tags]
            if len(similar_tags) > 0:
                for i in range(num_similar_tags_to_include):
                    sim_tag_data = self.recording_search_by_tag.search(
                        (self.tags[0], similar_tags[i]), "AND", start, stop,
                        self.NUM_RECORDINGS_TO_COLLECT)
                    if len(sim_tag_data) > self.NUM_RECORDINGS_TO_COLLECT:
                        sim_tag_data = sim_tag_data.random_item( start, stop, self.NUM_RECORDINGS_TO_COLLECT)

                    recordings.extend(sim_tag_data)

                if num_similar_tags_to_include > 1:
                    msgs = [
                        f"""tag: using seed tag '{self.tags[0]}' and similar tags '{"', '".join(similar_tags)}'."""
                    ]
                else:
                    msgs = [
                        f"""tag: using seed tag '{self.tags[0]}' and similar tag '{similar_tags[0]}'."""
                    ]
            else:
                msgs = [f"""tag: using only seed tag '{self.tags[0]}'."""]


        recordings = list(recordings)
        shuffle(recordings)
        return recordings, msgs


    def read(self, entities):

        self.recording_search_by_tag = self.patch.get_service(
            "recording-search-by-tag")

        self.local_storage["data_cache"]["element-descriptions"].append(
            f'tag{"" if len(self.tags) == 1 else "s"} {", ".join(self.tags)}')

        recordings, feedback = self.select_recordings()
        for msg in feedback:
            self.local_storage["user_feedback"].append(msg)

        return recordings
