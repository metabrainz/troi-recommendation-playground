from random import randint, shuffle
from uuid import UUID

import requests
from urllib.parse import quote

import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi.playlist import PlaylistMakerElement
from troi.parse_prompt import parse, ParseError, TIME_RANGES
from troi.patches.lb_radio_classes.artist import LBRadioArtistRecordingElement
from troi.patches.lb_radio_classes.blend import InterleaveRecordingsElement, WeighAndBlendRecordingsElement
from troi.patches.lb_radio_classes.collection import LBRadioCollectionRecordingElement
from troi.patches.lb_radio_classes.playlist import LBRadioPlaylistRecordingElement
from troi.patches.lb_radio_classes.tag import LBRadioTagRecordingElement
from troi.patches.lb_radio_classes.user import LBRadioUserRecordingElement
from troi import TARGET_NUMBER_OF_RECORDINGS


class LBRadioPatch(troi.patch.Patch):
    """
       ListenBrainz radio experimentation.
    """

    # If the user specifies no time_range, default to this one
    DEFAULT_TIME_RANGE = "month"

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
        """ Fetch artist names for validation purposes """

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

        # First parse the prompt
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

        # Save descriptions to local storage
        self.local_storage["data_cache"] = {"element-descriptions": [], "prompt": self.prompt}
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

            if element["entity"] == "artist":
                include_sim = False if "nosim" in element["opts"] else True
                source = LBRadioArtistRecordingElement(element["values"][0], mode=mode, include_similar_artists=include_sim)

            if element["entity"] == "tag":
                source = LBRadioTagRecordingElement(element["values"], mode=mode, operator="and")

            if element["entity"] == "tag-or":
                source = LBRadioTagRecordingElement(element["values"], mode=mode, operator="or")

            if element["entity"] == "collection":
                source = LBRadioCollectionRecordingElement(element["values"][0], mode=mode)

            if element["entity"] == "playlist":
                source = LBRadioPlaylistRecordingElement(element["values"][0], mode=mode)

            if element["entity"] == "user":
                if len(element["opts"]) == 0:
                    element["opts"].append(self.DEFAULT_TIME_RANGE)
                if len(element["values"]) == 0:
                    raise RuntimeError("user name cannot be blank for user entity. (at least not yet -- soon it will be)")
                if len(element["opts"]) != 1:
                    raise RuntimeError("The user entity needs to define one time range option.")
                source = LBRadioUserRecordingElement(element["values"][0], mode=mode, time_range=element["opts"][0])

            recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
            recs_lookup.set_sources(source)

            hate_filter = troi.filters.HatedRecordingsFilterElement()
            hate_filter.set_sources(recs_lookup)

            elements.append(hate_filter)

        # Finish the pipeline with the element that blends and weighs the streams
        blend = WeighAndBlendRecordingsElement(weights, max_num_recordings=100)
        blend.set_sources(elements)

        pl_maker = PlaylistMakerElement(patch_slug=self.slug(), max_num_recordings=TARGET_NUMBER_OF_RECORDINGS)
        pl_maker.set_sources(blend)

        return pl_maker

    def post_process(self):
        """ 
            Take the information saved in local_storage and create proper playlist names and descriptions.
        """

        prompt = self.local_storage["data_cache"]["prompt"]
        names = ", ".join(self.local_storage["data_cache"]["element-descriptions"])
        name = f"LB Radio for {names} on {self.mode} mode"
        desc = "Experimental ListenBrainz radio using %s mode, which was generated from this prompt: '%s'" % (self.mode, prompt)
        self.local_storage["_playlist_name"] = name
        self.local_storage["_playlist_desc"] = desc
