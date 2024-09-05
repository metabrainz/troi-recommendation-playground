from time import sleep
from random import randint, shuffle
from uuid import UUID

import requests
from urllib.parse import quote

import troi.patch
import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi.playlist import PlaylistMakerElement
from troi.parse_prompt import PromptParser, ParseError, TIME_RANGES
from troi.patches.lb_radio_classes.artist import LBRadioArtistRecordingElement
from troi.patches.lb_radio_classes.blend import InterleaveRecordingsElement, WeighAndBlendRecordingsElement
from troi.patches.lb_radio_classes.collection import LBRadioCollectionRecordingElement
from troi.patches.lb_radio_classes.playlist import LBRadioPlaylistRecordingElement
from troi.patches.lb_radio_classes.tag import LBRadioTagRecordingElement
from troi.patches.lb_radio_classes.stats import LBRadioStatsRecordingElement
from troi.patches.lb_radio_classes.recs import LBRadioRecommendationRecordingElement
from troi.patches.lb_radio_classes.country import LBRadioCountryRecordingElement
from troi import TARGET_NUMBER_OF_RECORDINGS, Playlist
from troi.utils import interleave


class LBRadioPatch(troi.patch.Patch):
    """
       ListenBrainz radio experimentation.
    """

    # If the user specifies no time_range, default to this one
    DEFAULT_TIME_RANGE = "month"

    def __init__(self, args):
        self.artist_mbids = []
        self.mode = None

        # Remember, the create function for this class will be called in the super() init.
        super().__init__(args)

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

    def lookup_artist(self, artist_name):
        """ Fetch artist names for validation purposes """

        if isinstance(artist_name, UUID):
            return self.lookup_artist_from_mbid(artist_name)

        err_msg = f"Artist {artist_name} could not be looked up. Please use exact spelling."

        while True:
            r = requests.get( f"https://musicbrainz.org/ws/2/artist?query={quote(artist_name)}&fmt=json")
            if r.status_code == 404:
                raise RuntimeError(err_msg)

            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise RuntimeError( f"Could not resolve artist name {artist_name}. Error {r.status_code} {r.text}")

            break

        data = r.json()
        try:
            fetched_name = data["artists"][0]["name"]
            mbid = data["artists"][0]["id"]
        except (IndexError, KeyError):
            raise RuntimeError(err_msg)

        if fetched_name.lower() == artist_name.lower():
            return fetched_name, mbid

        raise RuntimeError(err_msg)

    def lookup_artist_from_mbid(self, artist_mbid):
        """ Fetch artist names for validation purposes """

        while True:
            r = requests.get(f"https://musicbrainz.org/ws/2/artist/%s?fmt=json" % str(artist_mbid))
            if r.status_code == 404:
                raise RuntimeError(f"Could not resolve artist mbid {artist_mbid}. Error {r.status_code} {r.text}")

            if r.status_code in (429, 503):
                sleep(2)
                continue

            if r.status_code != 200:
                raise RuntimeError(f"Could not resolve artist name {artist_mbid}. Error {r.status_code} {r.text}")

            break

        return r.json()["name"], artist_mbid

    def create(self, inputs):
        self.prompt = inputs["prompt"]
        self.mode = inputs["mode"]

        # First parse the prompt
        pp = PromptParser()
        try:
            prompt_elements = pp.parse(self.prompt)
        except ParseError as err:
            raise RuntimeError(f"cannot parse prompt: '{err}'")

        if self.mode not in ("easy", "medium", "hard"):
            raise RuntimeError(
                "Argument mode must be one one easy, medium or hard.")

        # Lookup artist names embedded in the prompt
        artist_names = {}
        for element in prompt_elements:
            if element["entity"] == "artist":
                name, mbid = self.lookup_artist(element["values"][0])
                element["values"][0] = mbid
                artist_names[mbid] = name

        # Save descriptions to local storage
        self.local_storage["data_cache"] = {
            "element-descriptions": [],
            "prompt": self.prompt
        }
        self.local_storage["user_feedback"] = []

        weights = [e["weight"] for e in prompt_elements]

        # Now create the graph, based on the mode and the entities desired
        elements = []
        for element in prompt_elements:
            mode = self.mode
            if "easy" in element["opts"]:
                mode = "easy"
            elif "medium" in element["opts"]:
                mode = "medium"
            if "hard" in element["opts"]:
                mode = "hard"

            # Determine percent ranges based on mode -- this will likely need further tweaking
            if mode == "easy":
                start, stop = 0, 33
            elif self.mode == "medium":
                start, stop = 33, 66
            else:
                start, stop = 66, 100
            self.local_storage["modes"] = {
                "easy": (0, 33),
                "medium": (33, 66),
                "hard": (66, 100)
            }

            if element["entity"] == "artist":
                include_sim = False if "nosim" in element["opts"] else True
                source = LBRadioArtistRecordingElement(
                    element["values"][0],
                    artist_name=artist_names[element["values"][0]],
                    mode=mode,
                    include_similar_artists=include_sim)

            if element["entity"] == "tag":
                include_sim = False if "nosim" in element["opts"] else True
                operator = "or" if "or" in element["opts"] else "and"
                source = LBRadioTagRecordingElement(
                    [ t.lower() for t in element["values"]],
                    mode=mode,
                    operator=operator,
                    include_similar_tags=include_sim)

            if element["entity"] == "country":
                if isinstance(element["values"][0], UUID):
                    source = LBRadioCountryRecordingElement(
                        mode, 
                        area_mbid=element["values"][0])
                else:
                    source = LBRadioCountryRecordingElement(
                        mode, 
                        area_name=element["values"][0])

            if element["entity"] == "collection":
                source = LBRadioCollectionRecordingElement(
                    element["values"][0], mode=mode)

            if element["entity"] == "playlist":
                source = LBRadioPlaylistRecordingElement(element["values"][0],
                                                         mode=mode)

            if element["entity"] == "stats":
                if len(element["opts"]) == 0:
                    element["opts"].append(self.DEFAULT_TIME_RANGE)
                if len(element["values"]) == 0:
                    raise RuntimeError(
                        "user name cannot be blank for user entity. (at least not yet -- soon it will be)"
                    )
                if len(element["opts"]) != 1:
                    raise RuntimeError(
                        "The user entity needs to define one time range option."
                    )
                source = LBRadioStatsRecordingElement(
                    element["values"][0],
                    mode=mode,
                    time_range=element["opts"][0])

            if element["entity"] == "recs":
                if len(element["values"]) == 0:
                    raise RuntimeError(
                        "user name cannot be blank for user entity. (at least not yet -- soon it will be)"
                    )
                if len(element["opts"]) == 0:
                    listened = "all"
                else:
                    listened = element["opts"][0]
                source = LBRadioRecommendationRecordingElement(
                    element["values"][0], mode=mode, listened=listened)

            recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement(
            )
            recs_lookup.set_sources(source)

            hate_filter = troi.filters.HatedRecordingsFilterElement()
            hate_filter.set_sources(recs_lookup)

            elements.append(hate_filter)

        # Finish the pipeline with the element that blends and weighs the streams
        blend = WeighAndBlendRecordingsElement(weights, max_num_recordings=100, max_artist_occurrence=3)
        blend.set_sources(elements)

        pl_maker = PlaylistMakerElement(
            patch_slug=self.slug(),
            max_num_recordings=TARGET_NUMBER_OF_RECORDINGS)
        pl_maker.set_sources(blend)

        return pl_maker

    def post_process(self):
        """ 
            Take the information saved in local_storage and create proper playlist names and descriptions.
        """

        prompt = self.local_storage["data_cache"]["prompt"]
        names = ", ".join(
            self.local_storage["data_cache"]["element-descriptions"])
        name = f"LB Radio for {names} on {self.mode} mode"
        desc = "Experimental ListenBrainz radio using %s mode, which was generated from this prompt: '%s'" % (
            self.mode, prompt)
        self.local_storage["_playlist_name"] = name
        self.local_storage["_playlist_desc"] = desc
