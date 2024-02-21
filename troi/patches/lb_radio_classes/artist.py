import requests

import troi
from troi import Recording, Artist
from troi.splitter import plist
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

    def __init__(self, artist_mbid, mode="easy", include_similar_artists=True):
        troi.Element.__init__(self)
        self.artist_mbid = str(artist_mbid)
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

    def fetch_artist_names(self, artist_mbids):
        """
            Fetch artists names for a given list of artist_mbids 
        """

        # TODO: Use the artist cache data
        data = [{"[artist_mbid]": mbid} for mbid in artist_mbids]
        r = requests.post("https://datasets.listenbrainz.org/artist-lookup/json", json=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot artist names: {r.status_code} ({r.text})")

        return {result["artist_mbid"]: result["artist_name"] for result in r.json()}

    def read(self, entities):

        self.data_cache = self.local_storage["data_cache"]

        # Fetch our mode ranges
        start, stop = self.local_storage["modes"][self.mode]

        # TODO: Work out what to do about overhyped artists
        self.recording_search_by_artist = self.patch.get_service(
            "recording-search-by-artist")

        artist_recordings = self.recording_search_by_artist.search(self.artist_mbid, start, stop, self.max_top_recordings_per_artist, self.MAX_NUM_SIMILAR_ARTISTS)

        # For all fetched artists, fetch their names
        artist_names = self.fetch_artist_names(list(artist_recordings))
        for artist_mbid in artist_recordings:
            if artist_mbid not in artist_names:
                raise RuntimeError("Artist %s could not be found. Is this MBID valid?" % artist["artist_mbid"])

            # Store data in cache, so the post processor can create decent descriptions, title
            self.data_cache[artist_mbid] = artist_names[artist_mbid]

        # start crafting user feedback messages
        msgs = []
        if self.include_similar_artists and len(artist_recordings) == 1:
            msgs.append(f"Seed artist {artist_names[self.artist_mbid]} no similar artists.")
        else:
            if self.include_similar_artists and len(artist_recordings) < 4:
                msgs.append(f"Seed artist {artist_names[self.artist_mbid]} few similar artists.")
            msg = "artist: using seed artist %s" % artist_names[self.artist_mbid]
            if self.include_similar_artists:
                mbids = list(artist_recordings)
                del mbids[mbids.index(self.artist_mbid)]
                msg += " and similar artists: " + ", ".join([artist_names[mbid] for mbid in mbids])
            else:
                msg += " only"
            msgs.append(msg)

        for msg in msgs:
            self.local_storage["user_feedback"].append(msg)
        self.data_cache["element-descriptions"].append("artist %s" % artist_names[self.artist_mbid])


        # Now collect recordings from the artist and similar artists and return an interleaved
        # stream of recordings.
        for i, artist_mbid in enumerate(artist_recordings):

            recs_plist = plist(artist_recordings[artist_mbid])
            if len(recs_plist) < 20:
                self.local_storage["user_feedback"].append(
                    f"Artist {artist_names[artist_mbid]} only has {'no' if len(recs_plist) == 0 else 'few'} top recordings.")

            recordings = recs_plist.random_item(start, stop, self.max_top_recordings_per_artist)

        return interleave([artist_recordings[mbid] for mbid in artist_recordings])
