from abc import abstractmethod
from collections import defaultdict
from datetime import datetime
from random import randint, shuffle
from datetime import datetime

import requests

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
]


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


class LBRadioTagRecordingElement(troi.Element):


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

        data = [{"[tag]": tag, "operator": operator, "threshold": threshold } for tag in tags]
        r = requests.post("https://datasets.listenbrainz.org/recording-from-tag/json", json=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch recordings for tags. {r.text}")

        return list(r.json())

    def read(self, entities):
        threshold = 1

        recordings = []
        for rec in self.fetch_tag_data(self.tags, self.operator, threshold):
            recordings.append(Recording(mbid=rec["recording_mbid"]))

        return recordings


class LBRadioArtistRecordingElement(troi.Element):

    MAX_TOP_RECORDINGS_PER_ARTIST = 35  # should lower this when other sources of data get added
    MAX_NUM_SIMILAR_ARTISTS = 12

    def __init__(self, artist_mbid, mode="easy", weight=1):
        troi.Element.__init__(self)
        self.artist_mbid = artist_mbid
        self.artist_name = None
        self.similar_artists = []
        self.mode = mode
        self.weight = weight

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

        if "data_cache" not in self.local_storage:
            self.local_storage["data_cache"] = {"seed_artists": []}
        self.data_cache = self.local_storage["data_cache"]

        # Fetch similar artists for original artist
        similar_artists = self.get_similar_artists(self.artist_mbid)
        if len(similar_artists) == 0:
            raise RuntimeError("Not enough similar artist data available for artist %s. Please choose a different artist." %
                               self.entity_name)

        # Verify and lookup artist mbids
        artists = [{"mbid": self.artist_mbid}]
        for artist in similar_artists[:self.MAX_NUM_SIMILAR_ARTISTS]:
            artists.append({"mbid": artist["artist_mbid"]})

        artist_names = self.fetch_artist_names([i["mbid"] for i in artists])
        for artist in artists:
            if artist["mbid"] not in artist_names:
                raise RuntimeError("Artist %s could not be found. Is this MBID valid?" % artist_mbid)

            artist["name"] = artist_names[artist["mbid"]]

            # Store data in cache, so the post processor can create decent descriptions, title
            self.data_cache["seed_artists"].append((artist["name"], artist["mbid"]))
            self.data_cache[artist["mbid"]] = artist["name"]

        print("Seed artist: %s" % artists[0]["name"])

        if self.mode == "easy":
            start, stop = 0, 50
        elif self.mode == "medium":
            start, stop = 25, 75
            start, stop = 50, 100

        for i, artist in enumerate(artists):
            if artist["mbid"] + "_top_recordings" in self.data_cache:
                artist["recordings"] = self.data_cache[similar_artist["artist_mbid"] + "_top_recordings"]
                continue

            mbid_plist = plist(self.fetch_top_recordings(artist["mbid"]))
            recordings = []

            for recording in mbid_plist.random_item(start, stop, self.MAX_TOP_RECORDINGS_PER_ARTIST):
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

    def create(self, inputs):
        self.prompt = inputs["prompt"][0]
        self.mode = inputs["mode"]

        try:
            prompt_elements = parse(self.prompt)
        except ParseError as err:
            raise RuntimeError(f"cannot parse prompt: '{err}'")

        if self.mode not in ("easy", "medium", "hard"):
            raise RuntimeError("Argument mode must be one one easy, medium or hard.")

        elements = []
        for element in prompt_elements:
            if element["entity"] == "artist":
                source = LBRadioArtistRecordingElement(element["values"][0], self.mode, element["weight"])

            if element["entity"] == "tag":
                source = LBRadioTagRecordingElement(element["values"], mode=self.mode, operator="and", weight=element["weight"])

            if element["entity"] == "tag-or":
                source = LBRadioTagRecordingElement(element["values"], mode=self.mode, operator="or", weight=element["weight"])

            recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
            recs_lookup.set_sources(source)

            hate_filter = troi.filters.HatedRecordingsFilterElement()
            hate_filter.set_sources(recs_lookup)

            elements.append(hate_filter)

        #TODO: Add a duplicate filter
        interleave = InterleaveRecordingsElement()
        interleave.set_sources(elements)

        pl_maker = PlaylistMakerElement(patch_slug=self.slug(), max_num_recordings=50, max_artist_occurrence=5)
        pl_maker.set_sources(interleave)

        return pl_maker

    def post_process(self):

        names = [self.local_storage["data_cache"][mbid] for mbid in self.artist_mbids]
        name = "Artist Radio for " + ", ".join(names)
        desc = "Experimental artist radio using %s mode, which contains tracks from the seed artists (%s) and artists similar to them." % (
            self.mode, ", ".join(names))
        self.local_storage["_playlist_name"] = name
        self.local_storage["_playlist_desc"] = desc
