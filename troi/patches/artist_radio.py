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


class UnionElement(troi.Element):

    def __init__(self):
        troi.Element.__init__(self)

    def inputs(self):
        return []

    def outputs(self):
        return []

    def read(self, entities):

        recordings = []
        for entity in entities:
            recordings.extend(entity)

        return recordings


class PopularRecordingsElement(troi.Element):

    server_url = "https://datasets.listenbrainz.org/popular-recordings/json"

    def __init__(self, max_num_recordings=3):
        troi.Element.__init__(self)
        self.max_num_recordings = max_num_recordings

    def inputs(self):
        return [Artist]

    def outputs(self):
        return [Recording]

    def read(self, entities):

        for a in entities[0]:
            print(a.mbids)

        r = requests.post(self.server_url, json=[ { "[artist_mbid]" : a.mbids[0] } for a in entities[0] ])
        if r.status_code != 200:
            raise PipelineError("Cannot fetch popular recordings from ListenBrainz. HTTP code %s (%s)" % (r.status_code, r.text))

        output = []
        for row in r.json():
            output.append(Recording(mbid=row["recording_mbid"]))
            if len(output) >= self.max_num_recordings:
                break

        return output


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

        elements = []
        for artist_mbid in artist_mbids:
            elements.append(DataSetFetcherElement(server_url="https://labs.api.listenbrainz.org/similar-artists/json",
                                     max_num_items=5,
                                     json_post_data=[{
                                         'artist_mbid': artist_mbid,
                                         'algorithm': "session_based_days_1800_session_300_contribution_3_threshold_10_limit_100_filter_True_skip_30"
                                     }]))

        union = UnionElement()
        union.set_sources(elements)

        pop_recordings = PopularRecordingsElement(max_num_recordings=3)
        pop_recordings.set_sources(union)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(pop_recordings)

        pl_maker = PlaylistMakerElement(name="Artist Radio for %s" % (",".join(artist_mbids)),
                                        desc="Experimental artist radio playlist",
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=2,
                                        shuffle=True)
        pl_maker.set_sources(recs_lookup)

        return pl_maker
