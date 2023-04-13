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
from troi.splitter import DataSetSplitter
from troi.playlist import PlaylistMakerElement
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement

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


class ArtistRadioSourceElement(troi.Element):

    SIMILAR_ARTISTS_MINIMUM_COUNT = 500
    MAX_NUM_SIMILAR_ARTISTS = 20
    MAX_TOP_RECORDINGS_PER_ARTIST = 20
    KEEP_TOP_RECORDINGS_PER_ARTIST = 100

    def __init__(self, artist_mbid, mode="easy"):
        troi.Element.__init__(self)
        self.artist_mbid = artist_mbid
        self.similar_artists = []
        self.mode = mode

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def fetch_top_recordings(self, artist_mbid):

        r = requests.post("https://datasets.listenbrainz.org/popular-recordings/json", json=[{
            '[artist_mbid]': artist_mbid,
        }])
        return r.json()

    def get_similar_artists(self, artist_mbid):

        r = requests.post("https://labs.api.listenbrainz.org/similar-artists/json",
                          json=[{
                              'artist_mbid':
                              artist_mbid,
                              'algorithm':
                              "session_based_days_7500_session_300_contribution_5_threshold_10_limit_100_filter_True_skip_30"
                          }])

        try:
            artists = r.json()[3]["data"]
        except IndexError:
            return [], None

        artist_name = r.json()[1]["data"][0]["name"]

        return artists, artist_name

    def read(self, entities):

        # Fetch similar artists for original artist
        similar_artist_data, artist_name = self.get_similar_artists(self.artist_mbid)

        print("seed artist '%s'" % artist_name)
        if "artist_index" not in self.local_storage:
            self.local_storage["artist_index"] = {}

        self.local_storage["artist_index"][self.artist_mbid] = artist_name

        # Start collecting data
        self.similar_artists = []
        dss = DataSetSplitter(similar_artist_data, 4)

        if self.mode == "easy":
            segments = (0, 1)
        elif self.mode == "medium":
            segments = (1, 2)
        else:
            segments = (2, 3)

        for similar_artist in dss[segments[0]] + dss[segments[1]]:
            if similar_artist["score"] < self.SIMILAR_ARTISTS_MINIMUM_COUNT:
                print("  skip artist %s (count %d)" % (similar_artist["name"], similar_artist["score"]))
                continue

            recordings = self.fetch_top_recordings(similar_artist["artist_mbid"])
            if len(recordings) == 0:
                continue

            # Keep only a certain number of top recordings
            recordings = recordings[:self.KEEP_TOP_RECORDINGS_PER_ARTIST]

            self.similar_artists.append({
                "artist_mbid": similar_artist["artist_mbid"],
                "artist_name": similar_artist["name"],
                "raw_score": similar_artist["score"],
                "recordings": recordings,
                "dss": DataSetSplitter(recordings, 4, field="count")
            })

            if len(self.similar_artists) >= self.MAX_NUM_SIMILAR_ARTISTS:
                break

        # Normalize similar artist scores
        max_score = 0
        for sim in self.similar_artists:
            max_score = max(max_score, sim["raw_score"])

        for sim in self.similar_artists:
            sim["score"] = sim["raw_score"] / float(max_score)

            # And also normalize recording scores
            max_count = 0
            for rec in sim["recordings"]:
                max_count = max(max_count, rec["count"])

            for rec in sim["recordings"]:
                rec["count"] = rec["count"] / float(max_count)

            print("  similar: %.3f (%d) %d %s" % (sim["score"], sim["raw_score"], len(sim["recordings"]), sim["artist_name"]))

        # Now that data is collected, collate tracks into one single list
        recs = []
        print("Collate")
        for similar_artist in self.similar_artists:
            for index in segments:
                for recording in similar_artist["dss"][index]:
                    recs.append(recording)

        recs = sorted(recs, key=lambda k: k["count"], reverse=True)

        dss = DataSetSplitter(recs, 4, field="count")
        recordings = []
        for index in segments:
            for recording in dss.random_item(index, self.MAX_TOP_RECORDINGS_PER_ARTIST):
                recordings.append(Recording(mbid=recording["recording_mbid"]))

        return recordings


class ArtistRadioPatch(troi.patch.Patch):
    """
       Artist radio experimentation.
    """

    def __init__(self, debug=False):
        super().__init__(debug)
        self.artist_mbids = []

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
        return "artist-radio"

    @staticmethod
    def description():
        return "Given one or more artist_mbids, return a list playlist of those and similar artists."

    def create(self, inputs):
        self.artist_mbids = inputs["artist_mbid"]
        mode = inputs["mode"]

        if mode not in ("easy", "medium", "hard"):
            raise RuntimeError("Argument mode must be one one easy, medium or hard.")

        lookups = []
        for mbid in self.artist_mbids:
            ar_source = ArtistRadioSourceElement(mbid, mode)

            recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
            recs_lookup.set_sources(ar_source)

            lookups.append(recs_lookup)

        interleave = InterleaveRecordingsElement()
        interleave.set_sources(lookups)

        pl_maker = PlaylistMakerElement(desc="Experimental atist radio using %s mode." % mode,
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=5)
        pl_maker.set_sources(interleave)

        return pl_maker

    def post_process(self):

        names = [ self.local_storage["artist_index"][mbid] for mbid in self.artist_mbids]
        name = "Artist Radio for " + ", ".join(names)
        self.local_storage["_playlist_name"] = name
