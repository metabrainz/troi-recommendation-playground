from collections import defaultdict
import datetime
import random

from troi import Element, Recording, Playlist, PipelineError
import troi.listenbrainz.recs
import troi.filters
import troi.sorts
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup


class DecadePlaylistSplitterElement(Element):
    '''
        Split a list of recordings that have their year attribute filled out
        and output N playlists broken down by decade of the Recordings. Recordings
        with no year set will be ignored and playlists will only be generated
        for decades that have at least minimum_count recordings.
    '''

    def __init__(self, minimum_count=20):
        Element.__init__(self)
        self.minimum_count = minimum_count

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs = []):
        """
            Sort the recordings into decades and return playlists for decades that have the minimum number of tracks.
        """
        recordings = inputs[0]
        if not recordings or len(recordings) == 0:
            return []

        decades = defaultdict([])
        for r in recordings:
            if not r.year:
                continue

            decade = (r.year // 10) * 10
            decades[decade].append(r)

        playlists = []
        for decade in decades:
            if len(decade) < self.minmum_count:
                continue

            playlists.append(Playlist("%ss flashback jams", desc="ListenBrainz Weekly flashback jams for the %ss.", filename="%ss_flashback_jams.jspf"),
                             recordings=random.shuffle(decade))

        return playlists


class WeeklyFlashbackJams(troi.patch.Patch):

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "user_name", "desc": "ListenBrainz user name", "optional": False },
                { "type": str, "name": "type", "desc": "The type of daily jam. Must be 'top' or 'similar'.", "optional": False }]
        
    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "weekly-flashback-jams"

    @staticmethod
    def description():
        return "Generate a weekly playlist from the ListenBrainz recommended recordings based on decades."

    def create(self, inputs):
        user_name = inputs[0]
        type = inputs[1]

        if type not in ("top", "similar"):
            raise PipelineError("type must be either 'top' or 'similar'")

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                          artist_type=type,
                                                                          count=-1)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(recs)

        y_lookup = troi.musicbrainz.year_lookup.YearLookupElement()
        y_lookup.set_sources(r_lookup)

        # Filter out tracks that do not fit into the given year range
        year_sort = troi.sorts.YearSortElement()
        year_sort.set_sources(y_lookup)

        # If an artist should never appear in a playlist, add the artist_credit_id here
        artist_filter = troi.filters.ArtistCreditFilterElement([])
        artist_filter.set_sources(year_sort)

        decade_splitter = DecadePlaylistSplitterElement()
        decade_splitter.set_sources(artist_filter)
        
        artist_limiter = troi.filters.ArtistCreditLimiterElement(3)
        artist_limiter.set_sources(decade_splitter)

        return artist_limiter
