from collections import defaultdict
from datetime import datetime
from random import randint
from datetime import datetime

import requests

import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist, Element, Recording, Artist, PipelineError
from troi.playlist import PlaylistMakerElement
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement



class DataSetSplitter:

    def __init__(self, segment_count, field="score"):
        self.segment_count = segment_count
        self.field = field

    def split(self, data):

        if len(data) == 0:
            self.segments = []
            return
        self.data = data

        high_score = data[0][self.field]
        low_score = data[-1][self.field]

        segment_width = (high_score - low_score) / self.segment_count
        self.segments = []
        for segment in range(self.segment_count):
            self.segments.append({self.field: low_score + segment * segment_width})
        self.segments.reverse()

        segment_index = 0
        for i, d in enumerate(data):
            if d[self.field] < self.segments[segment_index][self.field]:
                self.segments[segment_index]["index"] = i - 1
                segment_index += 1

        self.segments[-1]["index"] = len(data) - 1
        print(self.segments)

    def items(self, segment):
        if segment < 0 or segment >= self.segment_count:
            raise ValueError("Invalid segment")

        if len(self.segments) == 0:
            return None

        if segment == 0:
            return self.data[0:self.segments[0]["index"]]
        else:
            return self.data[self.segments[segment - 1]["index"]:self.segments[segment]["index"]]

    def random_item(self, segment):
        if segment < 0 or segment >= self.segment_count:
            raise ValueError("Invalid segment")

        if len(self.segments) == 0:
            return None

        if segment == 0:
            data = self.data[0:self.segments[0]["index"]]
        else:
            data = self.data[self.segments[segment - 1]["index"]:self.segments[segment]["index"]]

        if len(data) == 0:
            return None
        
        return data[randint(0, len(data) - 1)]


def get_popular_recordings(artist_mbid):

    r = requests.post("https://datasets.listenbrainz.org/popular-recordings/json",
                      json=[{
                          '[artist_mbid]':
                          artist_mbid,
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

def collect_artists(artist_mbid):

    # Fetch similar artists for original artist
    orig_artists, original_artist_name = get_similar_artists(artist_mbid)
    if len(orig_artists) == 0:
        return []

    dss = DataSetSplitter(3)
    dss.split(orig_artists)

    print(orig_artists)

    artists = [ { "artist_mbid": artist_mbid, "name": original_artist_name, "score": 0 } ]
    artists.extend(dss.items(0))
    artists.extend(dss.items(1))

    # Now fetch similar artists for the A artists
    a_artists = dss.items(0)
    for artist in a_artists:
        sim_artists, sim_artist_name = get_similar_artists(artist["artist_mbid"])
        if len(sim_artists) == 0:
            continue
        d = DataSetSplitter(3)
        d.split(sim_artists)
        artists.extend(d.items(0))

    # Unique the list
    artists = list({a['artist_mbid']:a for a in artists}.values())

    return artists


def collect_recordings(artists):

    recordings = []

    for artist in artists:
        print("similar artists '%s'" % artist["name"])
        popular = get_popular_recordings(artist["artist_mbid"])
        ds = DataSetSplitter(4, "count")
        ds.split(popular)
        for j in range(3):
            try:
                for i in range(5):
                    item = ds.random_item(j)
                    if item is not None:
                        recordings.append(item)
            except ValueError:
                pass

        if len(recordings) > 150:
            break


    return list({r['recording_mbid']:r for r in recordings}.values())


class ArtistRadioSourceElement(troi.Element):

    def __init__(self, artist_mbids):
        troi.Element.__init__(self)
        self.artist_mbids = artist_mbids

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):
       
        artists = []
        for artist_mbid in self.artist_mbids:
            artists.append(collect_artists(artist_mbid))

        print(artists)
        artists = interleave(artists)

        recordings = collect_recordings(artists)
        recs = []
        for recording in recordings:
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
        return "artist-radio-2"

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
