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

    MAX_NUM_SIMILAR_ARTISTS = 10

    def __init__(self, artist_mbid):
        troi.Element.__init__(self)
        self.artist_mbid = artist_mbid
        self.similar_artists = []

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

        # Start collecting data
        self.similar_artists = []
        dss = DataSetSplitter(similar_artist_data, 3)
        for similar_artist in dss[0] + dss[1]:
            print("Fetch similar: ", similar_artist["artist_mbid"])
            recordings = self.fetch_top_recordings(similar_artist["artist_mbid"])
            self.similar_artists.append({ "artist_mbid": similar_artist["artist_mbid"], "recordings": recordings[:15] })

            if len(self.similar_artists) >= self.MAX_NUM_SIMILAR_ARTISTS:
                break


        # Now that data is collected, collate tracks into one single list
        recs = []
        print("Collate")
        while True:
            empty = 0
            for similar_artist in self.similar_artists:
                try:
                    recs.append(Recording(mbid=similar_artist["recordings"].pop(0)["recording_mbid"]))
                except IndexError:
                    empty += 1

            if empty == len(self.similar_artists):
                break

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


        lookups = []
        for mbid in artist_mbids:
            ar_source = ArtistRadioSourceElement(mbid)

            recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
            recs_lookup.set_sources(ar_source)

            lookups.append(recs_lookup)


        interleave = InterleaveRecordingsElement()
        interleave.set_sources(lookups)

        pl_maker = PlaylistMakerElement(name="Artist Radio for %s" % (",".join(artist_mbids)),
                                        desc="Experimental artist radio playlist",
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=5,
                                        shuffle=True)
        pl_maker.set_sources(interleave)

        return pl_maker
