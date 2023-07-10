from abc import abstractmethod
from collections import defaultdict
from datetime import datetime
from random import randint, shuffle
from datetime import datetime
from uuid import UUID

import requests
from urllib.parse import quote

import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist, Element, Recording, Artist, PipelineError
from troi.splitter import DataSetSplitter, plist
from troi.playlist import PlaylistMakerElement
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.parse_prompt import parse, ParseError

OVERHYPED_SIMILAR_ARTISTS = [
    "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",  # The Beatles
    "83d91898-7763-47d7-b03b-b92132375c47",  # Pink Floyd
    "a74b1b7f-71a5-4011-9441-d0b5e4122711",  # Radiohead
    "8bfac288-ccc5-448d-9573-c33ea2aa5c30",  # Red Hot Chili Peppers
    "9c9f1380-2516-4fc9-a3e6-f9f61941d090",  # Muse
    "cc197bad-dc9c-440d-a5b5-d52ba2e14234",  # Coldplay
    "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",  # Metallica
    "5b11f4ce-a62d-471e-81fc-a69a8278c7da",  # Nirvana
    "f59c5520-5f46-4d2c-b2c4-822eabf53419",  # Linkin Park
    "cc0b7089-c08d-4c10-b6b0-873582c17fd6",  # System of a Down
]
TARGET_NUMBER_OF_RECORDINGS = 50


def interleave(lists):
    return [val for tup in zip(*lists) for val in tup]


class InterleaveRecordingsElement(troi.Element):

    def __init__(self):
        troi.Element.__init__(self)

    def inputs(self):
        return [Recording]

    def outputs(self):
        return [Recording]

    def read(self, entities):

        recordings = []
        while True:
            empty = 0
            for entity in entities:
                try:
                    recordings.append(entity.pop(0))
                except IndexError:
                    empty += 1

            # Did we process all the recordings?
            if empty == len(entities):
                break

        return recordings


class WeighAndBlendRecordingsElement(troi.Element):

    def __init__(self, weights, max_num_recordings=TARGET_NUMBER_OF_RECORDINGS):
        troi.Element.__init__(self)
        self.weights = weights
        self.max_num_recordings = max_num_recordings

    def inputs(self):
        return [Recording]

    def outputs(self):
        return [Recording]

    def read(self, entities):

        total_available = sum([len(e) for e in entities])

        total = sum(self.weights)
        summed = []
        acc = 0
        for i in self.weights:
            acc += i
            summed.append(acc)

        # Ensure seed artists are the first tracks -- doing this for all recording elements work in this case.
        recordings = []
        for element in entities:
            try:
                recordings.append(element.pop(0))
            except IndexError:
                pass

        # This still allows sequential tracks to be from the same artists. I'll wait for feedback to see if this
        # is a problem.
        dedup_set = set()
        while True:
            r = randint(0, total)
            for i, s in enumerate(summed):
                if r < s:
                    while True:
                        if len(entities[i]) > 0:
                            rec = entities[i].pop(0)
                            if rec.mbid in dedup_set:
                                total_available -= 1
                                continue

                            recordings.append(rec)
                            dedup_set.add(rec.mbid)
                        break

            if len(recordings) >= self.max_num_recordings or len(recordings) == total_available:
                break

        return recordings


class LBRadioTagRecordingElement(troi.Element):

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2
    EASY_MODE_RELEASE_GROUP_MIN_TAG_COUNT = 4
    MEDIUM_MODE_ARTIST_MIN_TAG_COUNT = 4

    def __init__(self, tags, operator="and", mode="easy", weight=1):
        troi.Element.__init__(self)
        self.tags = tags
        self.operator = operator
        self.mode = mode
        self.weight = weight

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def fetch_tag_data(self, tags, operator, threshold):

        if self.mode == "easy":
            start, stop = 0, 50
        elif self.mode == "medium":
            start, stop = 25, 75
        else:
            start, stop = 50, 100

        data = {
            "condition": operator,
            "count": self.NUM_RECORDINGS_TO_COLLECT,
            "begin_percent": start / 100.0,
            "end_percent": stop / 100.0,
            "tag": tags,
            "threshold": threshold
        }
        r = requests.get("https://test-api.listenbrainz.org/1/tags", params=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch recordings for tags. {r.text}")

        return dict(r.json())

    def collect_recordings(self, recordings, tag_data, entity, min_tag_count=None):


        if min_tag_count is None:
            candidates = tag_data[entity]
        else:
            candidates = []
            for rec in tag_data[entity]:
                if rec["tag_count"] >= min_tag_count:
                    candidates.append(rec)

        tagged_with = f"tagged with '{', '.join(self.tags)}'"
        tag_count = f"highest tag count {tag_data[entity][0]['tag_count']}"
        if entity == "artist":
            if min_tag_count is None:
                msg = f"{tag_data['count']['artist']} recordings by artists {tagged_with}, {tag_count}"
            else:
                msg = f"{len(candidates)} recordings by artists {tagged_with} at least {min_tag_count} times, {tag_count}"
        elif entity == "release-group":
            if min_tag_count is None:
                msg = f"{tag_data['count']['release-group']} recordings on releases and release-groups {tagged_with}, {tag_count}"
            else:
                msg = f"{len(candidates)} recordings on releases and release-groups {tagged_with} at least {min_tag_count} times, {tag_count}"
        else:
            if min_tag_count is None:
                msg = f"{tag_data['count']['recording']} recordings {tagged_with}, {tag_count}"
            else:
                msg = f"{len(canidates)} recordings {tagged_with} at least {min_tag_count} times, {tag_count}"
        self.local_storage["user_feedback"].append(msg)

        while len(recordings) < self.NUM_RECORDINGS_TO_COLLECT and len(candidates) > 0:
            recordings.append(candidates.pop(randint(0, len(candidates) - 1)))

        return recordings, len(recordings) >= self.NUM_RECORDINGS_TO_COLLECT

    def read(self, entities):

        threshold = 1
        self.local_storage["data_cache"]["element-descriptions"].append(
            f'tag{"" if len(self.tags) == 1 else "s"} {", ".join(self.tags)}')

        tag_data = self.fetch_tag_data(self.tags, self.operator, threshold)

        recordings = plist()
        if self.mode == "easy":
            recordings, complete = self.collect_recordings(recordings, tag_data, "recording", min_tag_count=None)
            if not complete:
                recordings = self.collect_recordings(recordings,
                                                     tag_data,
                                                     "release-group",
                                                     min_tag_count=self.EASY_MODE_RELEASE_GROUP_MIN_TAG_COUNT)

                if len(recordings) < self.NUM_RECORDINGS_TO_COLLECT:
                    self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for easy mode." %
                                                               ", ".join(self.tags))
                    recordings = []

        elif self.mode == "medium":
            recordings, complete = self.collect_recordings(recordings, tag_data, "release-group", min_tag_count=None)
            if not complete:
                recordings = self.collect_recordings(recordings,
                                                     tag_data,
                                                     "artist",
                                                     min_tag_count=self.MEDIUM_MODE_RELEASE_GROUP_MIN_TAG_COUNT)

                if len(recordings) < self.NUM_RECORDINGS_TO_COLLECT:
                    self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for medium mode." %
                                                               ", ".join(self.tags))
                    recordings = []
        else:
            recordings, complete = self.collect_recordings(recordings, tag_data, "artist", min_tag_count=None)
            if len(recordings) < self.NUM_RECORDINGS_TO_COLLECT:
                self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for hard mode." %
                                                           ", ".join(self.tags))
                recordings = []

        # Convert results into recordings
        results = []
        for rec in recordings:
            results.append(Recording(mbid=rec["recording_mbid"]))

        return results


class LBRadioArtistRecordingElement(troi.Element):

    MAX_TOP_RECORDINGS_PER_ARTIST = 35  # should lower this when other sources of data get added
    MAX_NUM_SIMILAR_ARTISTS = 12

    def __init__(self, artist_mbid, mode="easy", weight=1, include_similar_artists=True):
        troi.Element.__init__(self)
        self.artist_mbid = str(artist_mbid)
        self.artist_name = None
        self.similar_artists = []
        self.mode = mode
        self.weight = weight
        self.include_similar_artists = include_similar_artists
        if include_similar_artists:
            self.max_top_recordings_per_artist = self.MAX_TOP_RECORDINGS_PER_ARTIST
        else:
            self.max_top_recordings_per_artist = self.MAX_TOP_RECORDINGS_PER_ARTIST * 2

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def get_similar_artists(self, artist_mbid):

        r = requests.post("https://labs.api.listenbrainz.org/similar-artists/json",
                          json=[{
                              'artist_mbid':
                              artist_mbid,
                              'algorithm':
                              "session_based_days_7500_session_300_contribution_5_threshold_10_limit_100_filter_True_skip_30"
                          }])
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch similar artists: {r.status_code} ({r.text})")

        try:
            artists = r.json()[3]["data"]
        except IndexError:
            return []

        # Knock down super hyped artists
        for artist in artists:
            if artist["artist_mbid"] in OVERHYPED_SIMILAR_ARTISTS:
                artist["score"] /= 3  # Chop!

        return plist(sorted(artists, key=lambda a: a["score"], reverse=True))

    def fetch_top_recordings(self, artist_mbid):

        r = requests.post("https://datasets.listenbrainz.org/popular-recordings/json", json=[{
            '[artist_mbid]': artist_mbid,
        }])
        return plist(r.json())

    def fetch_artist_names(self, artist_mbids):

        data = [{"[artist_mbid]": mbid} for mbid in artist_mbids]
        r = requests.post("https://datasets.listenbrainz.org/artist-lookup/json", json=data)

        return {result["artist_mbid"]: result["artist_name"] for result in r.json()}

    def read(self, entities):

        self.data_cache = self.local_storage["data_cache"]
        artists = [{"mbid": self.artist_mbid}]

        if self.include_similar_artists:
            # Fetch similar artists for original artist
            similar_artists = self.get_similar_artists(self.artist_mbid)
            if len(similar_artists) == 0:
                raise RuntimeError("Not enough similar artist data available for artist %s. Please choose a different artist." %
                                   self.artist_name)

            # Verify and lookup artist mbids
            for artist in similar_artists[:self.MAX_NUM_SIMILAR_ARTISTS]:
                artists.append({"mbid": artist["artist_mbid"]})

        artist_names = self.fetch_artist_names([i["mbid"] for i in artists])
        for artist in artists:
            if artist["mbid"] not in artist_names:
                raise RuntimeError("Artist %s could not be found. Is this MBID valid?" % artist_mbid)

            artist["name"] = artist_names[artist["mbid"]]

            # Store data in cache, so the post processor can create decent descriptions, title
            self.data_cache[artist["mbid"]] = artist["name"]

        print("Seed artist: %s" % artists[0]["name"])
        self.data_cache["element-descriptions"].append("artist %s" % artists[0]["name"])

        if self.mode == "easy":
            start, stop = 0, 50
        elif self.mode == "medium":
            start, stop = 25, 75
        else:
            start, stop = 50, 100

        for i, artist in enumerate(artists):
            if artist["mbid"] + "_top_recordings" in self.data_cache:
                artist["recordings"] = self.data_cache[artist["mbid"] + "_top_recordings"]
                continue

            mbid_plist = plist(self.fetch_top_recordings(artist["mbid"]))
            recordings = []

            for recording in mbid_plist.random_item(start, stop, self.max_top_recordings_per_artist):
                recordings.append(Recording(mbid=recording["recording_mbid"]))

            # Now tuck away the data for caching and interleaving
            self.data_cache[artist["mbid"] + "_top_recordings"] = recordings
            artist["recordings"] = recordings

        return interleave([a["recordings"] for a in artists])


class LBRadioPatch(troi.patch.Patch):
    """
       Artist radio experimentation.
    """

    def __init__(self, debug=False):
        super().__init__(debug)
        self.artist_mbids = []
        self.mode = None

    @staticmethod
    def inputs():
        """
        Generate a playlist from one or more Artist MBIDs

        \b
        MODE which mode to generate playlists in. must be one of easy, mediumedium, hard
        PROMPT is the LB radio prompt. See troi/parse_prompt.py for details.
        """
        return [{
            "type": "argument",
            "args": ["mode"],
            "kwargs": {
                "required": True,
                "nargs": 1
            }
        }, {
            "type": "argument",
            "args": ["prompt"],
            "kwargs": {
                "required": True,
                "nargs": 1
            }
        }]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "lb-radio"

    @staticmethod
    def description():
        return "Given an LB radio prompt, generate a playlist for that prompt."

    def lookup_artist_name(self, artist_name):

        err_msg = f"Artist {artist_name} could not be looked up. Please use exact spelling."

        r = requests.get(f"https://musicbrainz.org/ws/2/artist?query={quote(artist_name)}&fmt=json")
        if r.status_code == 404:
            raise RuntimeError(err_msg)

        if r.status_code != 200:
            raise RuntimeError(f"Could not resolve artist name {artist_name}. Error {r.status_code}")

        data = r.json()
        try:
            fetched_name = data["artists"][0]["name"]
            mbid = data["artists"][0]["id"]
        except (IndexError, KeyError):
            raise RuntimeError(err_msg)

        if fetched_name.lower() == artist_name.lower():
            return mbid

        raise RuntimeError(err_msg)

    def create(self, inputs):
        self.prompt = inputs["prompt"]
        self.mode = inputs["mode"]

        try:
            prompt_elements = parse(self.prompt)
        except ParseError as err:
            raise RuntimeError(f"cannot parse prompt: '{err}'")

        if self.mode not in ("easy", "medium", "hard"):
            raise RuntimeError("Argument mode must be one one easy, medium or hard.")

        # Lookup artist names embedded in the prompt
        for element in prompt_elements:
            if element["entity"] == "artist" and isinstance(element["values"][0], str):
                element["values"][0] = UUID(self.lookup_artist_name(element["values"][0]))

        self.local_storage["data_cache"] = {"element-descriptions": [], "prompt": self.prompt}
        self.local_storage["user_feedback"] = []

        weights = [e["weight"] for e in prompt_elements]

        elements = []
        for element in prompt_elements:
            mode = self.mode
            if "easy" in element["opts"]:
                mode = "easy"
            elif "medium" in element["opts"]:
                mode = "medium"
            if "hard" in element["opts"]:
                mode = "hard"

            if element["entity"] == "artist":
                include_sim = False if "nosim" in element["opts"] else True
                source = LBRadioArtistRecordingElement(element["values"][0],
                                                       mode=mode,
                                                       weight=element["weight"],
                                                       include_similar_artists=include_sim)

            if element["entity"] == "tag":
                source = LBRadioTagRecordingElement(element["values"], mode=mode, operator="and", weight=element["weight"])

            if element["entity"] == "tag-or":
                source = LBRadioTagRecordingElement(element["values"], mode=mode, operator="or", weight=element["weight"])

            recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
            recs_lookup.set_sources(source)

            hate_filter = troi.filters.HatedRecordingsFilterElement()
            hate_filter.set_sources(recs_lookup)

            elements.append(hate_filter)

        blend = WeighAndBlendRecordingsElement(weights, max_num_recordings=100)
        blend.set_sources(elements)

        pl_maker = PlaylistMakerElement(patch_slug=self.slug(), max_num_recordings=TARGET_NUMBER_OF_RECORDINGS)
        pl_maker.set_sources(blend)

        return pl_maker

    def post_process(self):

        prompt = self.local_storage["data_cache"]["prompt"]
        names = ", ".join(self.local_storage["data_cache"]["element-descriptions"])
        name = f"LB Radio for {names} on {self.mode} mode"
        desc = "Experimental ListenBrainz radio using %s mode, which was generated from this prompt: '%s'" % (self.mode, prompt)
        self.local_storage["_playlist_name"] = name
        self.local_storage["_playlist_desc"] = desc
