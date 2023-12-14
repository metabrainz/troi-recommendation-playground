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

        r = requests.post(
            "https://labs.api.listenbrainz.org/tag-similarity/json",
            json=[{
                "tag": tag
            }])
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch similar tags. {r.text}")

        return plist(r.json())

    def invert_for_tag_search(self, startstop):
        return tuple((1.0 - (startstop[1] / 100.), 1.0 - (startstop[0] / 100.0)))

    def select_recordings_on_easy(self):

        msgs = []
        start, stop = self.invert_for_tag_search(self.local_storage["modes"]["easy"])
        tag_data = self.recording_search_by_tag.search(self.tags,
                                                       self.operator,
                                                       start, stop)

        msgs = [f"""tag: using seed tags: '{ "', '".join(self.tags)}' only"""]
        return tag_data.random_item(start, stop,
                                    self.NUM_RECORDINGS_TO_COLLECT), msgs

    def select_recordings_on_medium(self):

        msgs = []
        start, stop = self.invert_for_tag_search(self.local_storage["modes"]["medium"])
        tag_data = self.recording_search_by_tag.search(self.tags,
                                                       self.operator,
                                                       start, stop)
        result = tag_data.random_item(start, stop,
                                      self.NUM_RECORDINGS_TO_COLLECT)

        if len(self.tags) == 1 and self.include_similar_tags:
            similar_tags = self.fetch_similar_tags(self.tags[0])
            similar_tag = similar_tags.random_item(0, 50, 1)
            if similar_tag is not None:
                similar_tag = similar_tag["similar_tag"]
                msgs = [
                    f"tag: using seed tag '{self.tags[0]}' and similar tag '{similar_tag}'."
                ]

                sim_tag_data = self.recording_search_by_tag.search(
                    [similar_tag], "OR", start, stop)

                return interleave((result, sim_tag_data)), msgs

        msgs = [f"""tag: using seed tags: '{ "', '".join(self.tags)}' only"""]
        return result, msgs

    def select_recordings_on_hard(self):

        msgs = []
        start, stop = self.invert_for_tag_search(self.local_storage["modes"]["hard"])
        tag_data = self.recording_search_by_tag.search(self.tags,
                                                       self.operator,
                                                       start, stop)
        result = tag_data.random_item(start, stop,
                                      self.NUM_RECORDINGS_TO_COLLECT)

        sim_start, sim_stop = 10, 50
        if len(self.tags) == 1 and self.include_similar_tags:
            similar_tags = self.fetch_similar_tags(self.tags[0])
            if len(similar_tags[sim_start:sim_stop]) > 2:
                while True:
                    selected_tags = similar_tags.random_item(10, 50, 2)
                    if selected_tags[0] == selected_tags[1]:
                        print("same tag selected!")
                        continue

                    break
                similar_tags = selected_tags
            else:
                similar_tags = similar_tags[sim_start:sim_stop]

            similar_tags = [tag["similar_tag"] for tag in similar_tags]

            if len(similar_tags) > 0:
                sim_tag_data = self.recording_search_by_tag.search(
                    (self.tags[0], similar_tags[0]), "AND", start, stop)

                if len(similar_tags) > 1:
                    sim_tag_data_2 = self.recording_search_by_tag.search(
                        (self.tags[0], similar_tags[1]), "AND", start, stop)
                    msgs = [
                        f"""tag: using seed tag '{self.tags[0]}' and similar tags '{"', '".join(similar_tags)}'."""
                    ]
                else:
                    msgs = [
                        f"""tag: using seed tag '{self.tags[0]}' and similar tag '{similar_tags[0]}'."""
                    ]
                    sim_tag_data_2 = []

                return interleave((result, sim_tag_data, sim_tag_data_2)), msgs
        else:
            msgs = [f"""tag: using only seed tag '{self.tags[0]}'."""]

        return result, msgs

    def read(self, entities):

        min_tag_count = self.TAG_THRESHOLD_MAPPING[self.mode]
        self.recording_search_by_tag = self.patch.get_service(
            "recording-search-by-tag")

        self.local_storage["data_cache"]["element-descriptions"].append(
            f'tag{"" if len(self.tags) == 1 else "s"} {", ".join(self.tags)}')

        recordings = plist()
        if self.mode == "easy":
            recordings, feedback = self.select_recordings_on_easy()
        elif self.mode == "medium":
            recordings, feedback = self.select_recordings_on_medium()
        else:
            recordings, feedback = self.select_recordings_on_hard()

        for msg in feedback:
            self.local_storage["user_feedback"].append(msg)

        # Convert results into recordings
        results = []
        for rec in recordings:
            if "subsonic_id" in rec:
                results.append(
                    Recording(mbid=rec["recording_mbid"],
                              musicbrainz={"subsonic_id": rec["subsonic_id"]}))
            else:
                results.append(Recording(mbid=rec["recording_mbid"]))

        return results
