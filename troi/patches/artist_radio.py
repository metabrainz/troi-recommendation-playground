from datetime import datetime

import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist, Element, Recording
from troi.playlist import PlaylistMakerElement
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement


class UnionElement(troi.Element):

    def __init__(self):
        troi.Element.__init__(self)

    def inputs(self):
        return []

    def read(self, entities):

        recordings = []
        for entity in entities:
            recordings.extend(entity)

        return recordings


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
            print(f'{artist_mbid}')
            elements.append(DataSetFetcherElement(server_url="https://labs.api.listenbrainz.org/similar-artists/json",
                                     json_post_data=[{
                                         'artist_mbid': artist_mbid,
                                         'algorithm': "session_based_days_1800_session_300_contribution_3_threshold_10_limit_100_filter_True_skip_30"
                                     }]))

        union = UnionElement()
        union.set_sources(elements)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(union)

        pl_maker = PlaylistMakerElement(name="Artist Radio for %s" % (",".join(artist_mbids)),
                                        desc="Experimental artist radio playlist",
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=2,
                                        shuffle=True)
        pl_maker.set_sources(recs_lookup)

        return pl_maker
