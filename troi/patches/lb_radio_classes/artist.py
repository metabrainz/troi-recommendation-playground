from time import sleep

import troi
from troi import Recording, Artist
from troi.plist import plist
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.utils import interleave
from troi.recording_search_service import RecordingSearchByArtistService


class LBRadioArtistRecordingElement(troi.Element):
    """
        Given an artist, find its similar artists and their popular tracks and return one 
        stream of recodings from it.
    """

    MAX_TOP_RECORDINGS_PER_ARTIST = 35  # should lower this when other sources of data get added
    MAX_NUM_SIMILAR_ARTISTS = 8
    MAX_NUM_RECORDINGS = 1000

    def __init__(self, artist_mbid, artist_name, mode="easy", include_similar_artists=True):
        troi.Element.__init__(self)
        self.artist_mbid = str(artist_mbid)
        self.artist_name = artist_name
        self.mode = mode
        self.include_similar_artists = include_similar_artists
        if include_similar_artists:
            self.max_top_recordings_per_artist = self.MAX_TOP_RECORDINGS_PER_ARTIST * 2
        else:
            self.max_top_recordings_per_artist = self.MAX_TOP_RECORDINGS_PER_ARTIST * 3

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        self.data_cache = self.local_storage["data_cache"]

        # Fetch our mode ranges
        start, stop = self.local_storage["modes"][self.mode]
        self.recording_search_by_artist = self.patch.get_service("recording-search-by-artist")
        if self.include_similar_artists:
            similar_artist_count = self.MAX_NUM_SIMILAR_ARTISTS
        else:
            similar_artist_count = 0

        (artist_recordings, msgs) = self.recording_search_by_artist.search(self.mode, self.artist_mbid, start, stop,
                                                                           self.max_top_recordings_per_artist,
                                                                           similar_artist_count)
        # Collect the names of the similar artists
        similar_artist_names = []
        for mbid in artist_recordings:
            if mbid == self.artist_mbid:
                continue

            try:
                similar_artist_names.append(artist_recordings[mbid][0].artist_credit.name)
                # The item may not exist, or the artist credit may be None
            except (AttributeError, IndexError):
                pass

        # craft user feedback messages
        if not artist_recordings:
            msgs.append(f"The seed artist %s has no similar artists, nor top recordings. Too niche?" % self.artist_name)
        else:
            msg = "Using seed artist %s" % self.artist_name
            if self.include_similar_artists:
                if similar_artist_names:
                    msg += " and similar artists: " + ", ".join(similar_artist_names)
                else:
                    msg += " only, since this artist has no similar artists (yet)."
            else:
                msg += " only"

            msgs.insert(0, msg)

        for msg in msgs:
            self.local_storage["user_feedback"].append(msg)
        self.data_cache["element-descriptions"].append("artist %s" % self.artist_name)

        return interleave([artist_recordings[mbid] for mbid in artist_recordings])[:self.MAX_NUM_RECORDINGS]
