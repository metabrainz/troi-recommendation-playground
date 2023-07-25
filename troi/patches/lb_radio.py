from abc import abstractmethod
from collections import defaultdict
from datetime import datetime
from random import randint, shuffle
from datetime import datetime
from uuid import UUID

import requests
from urllib.parse import quote

import pylistenbrainz
import pylistenbrainz.errors
import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist, Element, Recording, Artist, PipelineError
from troi.splitter import DataSetSplitter, plist
from troi.playlist import PlaylistMakerElement
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement
from troi.parse_prompt import parse, ParseError, TIME_RANGES

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
    """
        This element round-robins the various input sources into one list until all sources are all empty.
    """

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
    """
        This element will weight all the given sources according to weights passed to __init__ and
        then combine all the input sources into one weighted output stream.

        A source that has a weight of 2 will be chosen 2 times more often than a source with weight 1.
    """

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


class LBRadioUserRecordingElement(troi.Element):
    """
        Given a LB user, fetch their recording stats and then include recordings from it.
    """

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2

    def __init__(self, user_name, time_range, mode="easy"):
        troi.Element.__init__(self)
        self.user_name = user_name
        self.time_range = time_range
        self.mode = mode
        self.client = pylistenbrainz.ListenBrainz()

        if time_range not in TIME_RANGES:
            raise RuntimeError("entity user must specify one of the following time range options: " + ", ".join(TIME_RANGES))

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        if self.mode == "easy":
            offset = 0
        elif self.mode == "medium":
            offset = 100
        else:
            offset = 200

        try:
            result = self.client.get_user_recordings(self.user_name, 100, offset, self.time_range)
        except pylistenbrainz.errors.ListenBrainzAPIException as err:
            raise RuntimeError("Cannot fetch recording stats for user %s" % self.user_name)

        self.local_storage["data_cache"]["element-descriptions"].append(f"user {self.user_name} stats for {self.time_range}")

        recordings = []
        for r in result['payload']['recordings']:
            if r['recording_mbid'] is not None:
                recordings.append(Recording(mbid=r['recording_mbid']))

        shuffle(recordings)

        return recordings


class LBRadioPlaylistRecordingElement(troi.Element):
    """
        Given an LB playlist, fetch its tracks and randomly include recordiungs from it. mode does not
        apply to this element.
    """

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2

    def __init__(self, mbid, mode="easy"):
        troi.Element.__init__(self)
        self.mbid = mbid
        self.mode = mode

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):
        r = requests.get(f"https://api.listenbrainz.org/1/playlist/{self.mbid}")
        if r.status_code == 404:
            raise RuntimeError(f"Cannot find playlist {self.mbid}.")
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch playlist {self.mbid}. {r.text}")

        self.local_storage["data_cache"]["element-descriptions"].append(f"playlist {self.mbid}")
        # Fetch the recordings, then shuffle
        mbid_list = [r["identifier"][34:] for r in r.json()["playlist"]["track"]]
        shuffle(mbid_list)

        # Select and convert the first n MBIDs into Recordings
        recordings = []
        for mbid in mbid_list[:self.NUM_RECORDINGS_TO_COLLECT]:
            recordings.append(Recording(mbid=mbid))

        return recordings


class LBRadioCollectionRecordingElement(troi.Element):
    """
        Given an MB recording collection, fetch it and randomly include recordings from it. mode does not
        apply to this element.
    """

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2

    def __init__(self, mbid, mode="easy"):
        troi.Element.__init__(self)
        self.mbid = mbid
        self.mode = mode

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        params = {"collection": self.mbid, "fmt": "json"}
        r = requests.get("https://musicbrainz.org/ws/2/recording", params=params)
        if r.status_code == 404:
            raise RuntimeError(f"Cannot find collection {mbid}.")
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch collection {mbid}. {r.text}")

        self.local_storage["data_cache"]["element-descriptions"].append(f"collection {self.mbid}")

        # Fetch the recordings, then shuffle
        mbid_list = []
        for r in r.json()["recordings"]:
            if not r["video"]:
                mbid_list.append(r["id"])
        shuffle(mbid_list)

        # Select and convert the first n MBIDs into Recordings
        recordings = []
        for mbid in mbid_list[:self.NUM_RECORDINGS_TO_COLLECT]:
            recordings.append(Recording(mbid=mbid))

        return recordings


class LBRadioTagRecordingElement(troi.Element):

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2
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
                msg = f"{len(canidates):,} recordings {tagged_with} at least {min_tag_count} times, {tag_count}"
        self.local_storage["user_feedback"].append(msg)

        while len(recordings) < self.NUM_RECORDINGS_TO_COLLECT and len(candidates) > 0:
            recordings.append(candidates.pop(randint(0, len(candidates) - 1)))

        return recordings, len(recordings) >= self.NUM_RECORDINGS_TO_COLLECT

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
            entity = "recording"
            recordings, complete = self.collect_recordings(recordings, tag_data, entity, min_tag_count=None)
            complete = False
            if not complete:
                try:
                    highest_tag_count = tag_data[entity][0]["tag_count"]
                except IndexError:
                    highest_tag_count = 0
                lowest_tag_count = self.get_lowest_tag_count(highest_tag_count)
                print(f"tag range: {highest_tag_count} {lowest_tag_count}")
                for tag_count in range(highest_tag_count, lowest_tag_count, -1):
                    recordings, complete = self.collect_recordings(recordings, tag_data, "release-group", min_tag_count=tag_count)
                    if complete:
                        break

                if len(recordings) < self.NUM_RECORDINGS_TO_COLLECT:
                    self.local_storage["user_feedback"].append("tag '%s' generated too few recordings for easy mode." %
                                                               ", ".join(self.tags))
                    recordings = []

        elif self.mode == "medium":
            recordings, complete = self.collect_recordings(recordings, tag_data, "release-group", min_tag_count=None)
            entity = "release-group"
            complete = False
            if not complete:
                try:
                    highest_tag_count = tag_data[entity][0]["tag_count"]
                except IndexError:
                    highest_tag_count = 0
                lowest_tag_count = self.get_lowest_tag_count(highest_tag_count)
                print("tag range: {highest_tag_count} {lowest_tag_count}")
                for tag_count in range(highest_tag_count, lowest_tag_count, -1):
                    recordings = self.collect_recordings(recordings, tag_data, "artist", min_tag_count=tag_count)
                    if complete:
                        break

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
    """
        Given an artist, find its similar artists and their popular tracks and return one 
        stream of recodings from it.
    """

    MAX_TOP_RECORDINGS_PER_ARTIST = 35  # should lower this when other sources of data get added
    MAX_NUM_SIMILAR_ARTISTS = 12

    def __init__(self, artist_mbid, mode="easy", include_similar_artists=True):
        troi.Element.__init__(self)
        self.artist_mbid = str(artist_mbid)
        self.artist_name = None
        self.similar_artists = []
        self.mode = mode
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
        """ Fetch similar artists, given an artist_mbid. Returns a sored plist of artists. """

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
        """
            Given and artist_mbid, fetch top recordings for this artist and retun them in a plist.
        """

        r = requests.post("https://datasets.listenbrainz.org/popular-recordings/json", json=[{
            '[artist_mbid]': artist_mbid,
        }])
        return plist(r.json())

    def fetch_artist_names(self, artist_mbids):
        """
            Fetch artists names for a given list of artist_mbids 
        """

        data = [{"[artist_mbid]": mbid} for mbid in artist_mbids]
        r = requests.post("https://datasets.listenbrainz.org/artist-lookup/json", json=data)

        return {result["artist_mbid"]: result["artist_name"] for result in r.json()}

    def read(self, entities):

        self.data_cache = self.local_storage["data_cache"]
        artists = [{"mbid": self.artist_mbid}]

        # First, fetch similar artists if the user didn't override that.
        if self.include_similar_artists:
            # Fetch similar artists for original artist
            similar_artists = self.get_similar_artists(self.artist_mbid)
            if len(similar_artists) == 0:
                raise RuntimeError("Not enough similar artist data available for artist %s. Please choose a different artist." %
                                   self.artist_name)

            # Verify and lookup artist mbids
            for artist in similar_artists[:self.MAX_NUM_SIMILAR_ARTISTS]:
                artists.append({"mbid": artist["artist_mbid"]})

        # For all fetched artists, fetcht their names
        artist_names = self.fetch_artist_names([i["mbid"] for i in artists])
        for artist in artists:
            if artist["mbid"] not in artist_names:
                raise RuntimeError("Artist %s could not be found. Is this MBID valid?" % artist_mbid)

            artist["name"] = artist_names[artist["mbid"]]

            # Store data in cache, so the post processor can create decent descriptions, title
            self.data_cache[artist["mbid"]] = artist["name"]

        # start crafting user feedback messages
        msg = "artist: using seed artist %s" % artists[0]["name"]
        if self.include_similar_artists:
            msg += " and similar artists: " + ", ".join([a["name"] for a in artists[1:]])
        else:
            msg += " only"

        self.local_storage["user_feedback"].append(msg)
        self.data_cache["element-descriptions"].append("artist %s" % artists[0]["name"])

        # Deremine percent ranges based on mode -- this will likely need further tweaking
        if self.mode == "easy":
            start, stop = 0, 50
        elif self.mode == "medium":
            start, stop = 25, 75
        else:
            start, stop = 50, 100

        # Now collect recordings from the artist and similar artists and return an interleaved
        # strem of recordings.
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
                if len(element["values"]) == 0:
                        raise RuntimeError("user name cannot be blank for user entity.")
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
