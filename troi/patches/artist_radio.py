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

# Variables we can control:
#
# max counts, to ensure that we don't go too low 5 - 10 artists seems good.
#


def get_popular_recordings(artist_mbid):

    r = requests.post("https://datasets.listenbrainz.org/popular-recordings/json", json=[{
        '[artist_mbid]': artist_mbid,
    }])
    return r.json()


def get_similar_artists(artist_mbid):

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


def interleave(lists):
    return [val for tup in zip(*lists) for val in tup]


class ArtistRadioSourceElement(troi.Element):

    MAX_NUM_SIMILAR_ARTISTS = 10 

    def __init__(self, artist_mbids):
        troi.Element.__init__(self)
        self.artist_mbids = artist_mbids
        self.artists = {}

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def collect_artists(self, artist_mbid):

        # Fetch similar artists for original artist
        orig_artists, original_artist_name = get_similar_artists(artist_mbid)
        if len(orig_artists) == 0:
            return

        print("seed artist '%s'" % original_artist_name)

        dss = DataSetSplitter(orig_artists, 3)

        similar_artists = {}
        for artist in dss[0]:
            if len(similar_artists) > self.MAX_NUM_SIMILAR_ARTISTS:
                break

            if artist["artist_mbid"] not in self.artists:
                artist["level"] = 1
                similar_artists[artist["artist_mbid"]] = artist
                print("  0 %5d %s %s" % (artist["score"], artist["name"], artist["artist_mbid"]))


        for artist in dss[1]:
            if len(similar_artists) > self.MAX_NUM_SIMILAR_ARTISTS:
                break
            if artist["artist_mbid"] not in self.artists:
                artist["level"] = 2
                similar_artists[artist["artist_mbid"]] = artist
                print("  1 %5d %s %s" % (artist["score"], artist["name"], artist["artist_mbid"]))

        self.artists[artist_mbid] = {
            "artist_mbid": artist_mbid,
            "name": original_artist_name,
            "similar-artists": similar_artists,
            "level": 0,
            "score": 0
        }

        # Note: I tried loading more similar artists from the top artists, but the results were bad. Stick to 1 level.

    def collect_recordings(self):

        recordings = []

        all_artists = {}
        all_artists |= self.artists
        for mbid in self.artists:
            all_artists |= self.artists[mbid]["similar-artists"]

        for artist_mbid in all_artists:
            artist = all_artists[artist_mbid]
            popular = get_popular_recordings(artist["artist_mbid"])
            dss = DataSetSplitter(popular[:50], 6, "count")

            recordings = []
            for s in range(dss.get_segment_count() - 1):
                recordings.extend(dss[s])

            artist["recordings"] = recordings
            print("recs for artist '%s' %d recordings" % (artist["name"], len(artist["recordings"])))

    def read(self, entities):

        for artist_mbid in self.artist_mbids:
            if artist_mbid not in self.artists:
                self.collect_artists(artist_mbid)

        # Load all the recordings into the artists
        self.collect_recordings()

        for artist_mbid in self.artists:
            recordings = self.artists[artist_mbid]["recordings"]
            for sim_artist_mbid in self.artists[artist_mbid]["similar-artists"]:
                recordings.extend(self.artists[artist_mbid]["similar-artists"][sim_artist_mbid]["recordings"])

            self.artists[artist_mbid]["all_recordings"] = recordings

        # Shuffle the loaded tracks
        for artist_mbid in self.artists:
            shuffle(self.artists[artist_mbid]["all_recordings"])

        recs = []
        for artist_mbid in self.artists:
            artist = self.artists[artist_mbid]
            for i in range(10):
                recording = artist["all_recordings"].pop(0)
                recs.append(Recording(mbid=recording["recording_mbid"]))

        return recs


class ArtistRadioPatch(troi.patch.Patch):
    """
       Artist radio experimentation.
    """

    def __init__(self, debug=False):
        super().__init__(debug)

    @staticmethod
    def inputs():
        """
        Generate a playlist from one or more Artist MBIDs

        \b
        ARTIST_MBIDs is a list of artist_mbids to be used as seeds
        """
        return [{"type": "argument", "args": ["artist_mbid"], "kwargs": {"required": False, "nargs": -1}}]

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
        artist_mbids = inputs['artist_mbid']

        ar_source = ArtistRadioSourceElement(artist_mbids)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(ar_source)

        pl_maker = PlaylistMakerElement(name="Artist Radio for %s" % (",".join(artist_mbids)),
                                        desc="Experimental artist radio playlist",
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=5,
                                        shuffle=True)
        pl_maker.set_sources(recs_lookup)

        return pl_maker
