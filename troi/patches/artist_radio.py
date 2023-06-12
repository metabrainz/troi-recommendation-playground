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


class RecordingSource:

    def __init__(self, mode, entity_type, entity_name=None, entity_mbid=None, year=None):
        self.mode = mode
        self.entity_type = entity_type
        self.entity_name = entity_name
        self.entity_mbid = entity_mbid
        self.year = year

    @abstractmethod
    def get(self):
        pass


class SimilarArtistRecordingSource(RecordingSource):

    KEEP_TOP_RECORDINGS_PER_ARTIST = 100
    MAX_NUM_SIMILAR_ARTISTS = 20

    def __init__(self, mode, entity_type, entity_name="", entity_mbid="", data_cache=None):
        """
            entity_type, name and mbid must be given for this source
        """
        super().__init__(mode, entity_type, entity_name, entity_mbid)

        self.data_cache = data_cache

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

    def get(self):

        # Fetch similar artists for original artist
        artists_to_lookup = self.get_similar_artists(self.entity_mbid)
        if len(artists_to_lookup) == 0:
            raise RuntimeError("Not enough similar artist data available for artist %s. Please choose a different artist." %
                               self.entity_name)

        print("Seed artist: %s" % self.entity_name)

        self.data_cache[self.entity_mbid] = self.entity_name
        self.data_cache["seed_artists"].append((self.entity_name, self.entity_mbid))

        if self.mode == "easy":
            start, stop = 0, 50
        elif self.mode == "medium":
            start, stop = 25, 75
            start, stop = 50, 100

        similar_artist_recordings = []
        for i, similar_artist in enumerate(artists_to_lookup[start:stop]):
            #            if similar_artist["score"] < min_similar_artists:
            #                print("  skip artist %s (count %d)" % (similar_artist["name"], similar_artist["score"]))
            #                continue

            if similar_artist["artist_mbid"] + "_top_recordings" in self.data_cache:
                similar_artist_recordings.append(self.data_cache[similar_artist["artist_mbid"] + "_top_recordings"])
                continue

            recordings = self.fetch_top_recordings(similar_artist["artist_mbid"])
            if len(recordings) == 0:
                continue

            # Keep only a certain number of top recordings
            recordings = recordings.dslice(None, self.KEEP_TOP_RECORDINGS_PER_ARTIST)

            # normalize recording scores
            max_count = 0
            for rec in recordings:
                max_count = max(max_count, rec["count"])

            for rec in recordings:
                rec["score"] = rec["count"] / float(max_count)

            # Now tuck away the data for caching and interleaving
            self.data_cache[similar_artist["artist_mbid"] + "_top_recordings"] = recordings
            similar_artist_recordings.append(recordings)

            if i >= self.MAX_NUM_SIMILAR_ARTISTS:
                break

        return interleave(similar_artist_recordings)


class LBRadioSourceElement(troi.Element):

    MAX_TOP_RECORDINGS_PER_ARTIST = 50  # should lower this when other sources of data get added

    def __init__(self, artist_mbid, artist_name, mode="easy"):
        troi.Element.__init__(self)
        self.artist_mbid = artist_mbid
        self.artist_name = artist_name
        self.similar_artists = []
        self.mode = mode

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def fetch_artist_names(self, artist_mbid):

        r = requests.post("https://datasets.listenbrainz.org/artist-lookup/json", json=[{
            '[artist_mbid]': artist_mbid,
        }])

        return {r.artist_mbid: r.artist_name for result in r.json()}

    def read(self, entities):

        if "data_cache" not in self.local_storage:
            self.local_storage["data_cache"] = {"seed_artists": []}

        if self.mode == "easy":
            start, stop = 0, 50
        elif self.mode == "medium":
            start, stop = 25, 75
            start, stop = 50, 100

        sa = SimilarArtistRecordingSource(self.mode,
                                          "artist",
                                          entity_mbid=self.artist_mbid,
                                          entity_name=self.artist_name,
                                          data_cache=self.local_storage["data_cache"])
        seed_artist_recordings = plist(sa.fetch_top_recordings(self.artist_mbid))
        mbid_plist = plist(sorted(sa.get(), key=lambda k: k["count"], reverse=True))

        recordings = plist()
        recordings.append(Recording(mbid=seed_artist_recordings.random_item(0, 25)["recording_mbid"]))
        for recording in mbid_plist.random_item(start, stop, self.MAX_TOP_RECORDINGS_PER_ARTIST):
            recordings.append(Recording(mbid=recording["recording_mbid"]))

        return recordings


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
        ARTIST_MBIDs is a list of artist_mbids to be used as seeds
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
            "args": ["artist_mbid"],
            "kwargs": {
                "required": False,
                "nargs": -1
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

    def fetch_artist_names(self, artist_mbids):

        data = [{"[artist_mbid]": mbid} for mbid in artist_mbids]
        r = requests.post("https://datasets.listenbrainz.org/artist-lookup/json", json=data)

        return {result["artist_mbid"]: result["artist_name"] for result in r.json()}

    def create(self, inputs):
        self.artist_mbids = inputs["artist_mbid"]
        self.mode = inputs["mode"]

        self.artist_names = self.fetch_artist_names(self.artist_mbids)
        for artist_mbid in self.artist_mbids:
            if artist_mbid not in self.artist_names:
                raise RuntimeError("Artist %s could not be found. Is this MBID valid?" % artist_mbid)

        if self.mode not in ("easy", "medium", "hard"):
            raise RuntimeError("Argument mode must be one one easy, medium or hard.")

        lookups = []
        for mbid in self.artist_mbids:
            ar_source = LBRadioSourceElement(mbid, self.artist_names[mbid], self.mode)

            recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
            recs_lookup.set_sources(ar_source)

            hate_filter = troi.filters.HatedRecordingsFilterElement()
            hate_filter.set_sources(recs_lookup)

            lookups.append(hate_filter)

        interleave = InterleaveRecordingsElement()
        interleave.set_sources(lookups)

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
