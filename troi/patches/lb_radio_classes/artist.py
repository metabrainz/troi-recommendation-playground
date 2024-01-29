import requests

import troi
from troi import Recording, Artist
from troi.splitter import plist
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.utils import interleave
from troi.recording_search_service import RecordingSearchByArtistService

OVERHYPED_SIMILAR_ARTISTS = [
    "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",  # The Beatles
    "83d91898-7763-47d7-b03b-b92132375c47",  # Pink Floyd
    "a74b1b7f-71a5-4011-9441-d0b5e4122711",  # Radiohead
    "8bfac288-ccc5-448d-9573-c33ea2aa5c30",  # Red Hot Chili Peppers
    "9c9f1380-2516-4fc9-a3e6-f9f61941d090",  # Muse
    "cc197bad-dc9c-440d-a5b5-d52ba2e14234",  # Coldplay
    "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",  # Metallica
    "5b11f4ce-a62d-471e-81fc-a69a8278c7da",  # Nirvana
    "f59c5520-5f46-4d2c-b2c4-822eabf53419",  # Linkin Park
    "cc0b7089-c08d-4c10-b6b0-873582c17fd6",  # System of a Down
    "ebfc1398-8d96-47e3-82c3-f782abcdb13d",  # Beach boys
]


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
        self.artist_name = None
        self.similar_artists = []
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

    def get_similar_artists(self, artist_mbid):
        """ Fetch similar artists, given an artist_mbid. Returns a sored plist of artists. """

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

    def fetch_artist_names(self, artist_mbids):
        """
            Fetch artists names for a given list of artist_mbids 
        """

        data = [{"[artist_mbid]": mbid} for mbid in artist_mbids]
        r = requests.post("https://datasets.listenbrainz.org/artist-lookup/json", json=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot artist names: {r.status_code} ({r.text})")

        return {result["artist_mbid"]: result["artist_name"] for result in r.json()}

    def read(self, entities):

        # Fetch our mode ranges
        start, stop = self.local_storage["modes"][self.mode]

        self.data_cache = self.local_storage["data_cache"]
        artists = [{"mbid": self.artist_mbid}]

        self.recording_search_by_artist = self.patch.get_service(
            "recording-search-by-artist")

        # First, fetch similar artists if the user didn't override that.
        if self.include_similar_artists:
            # Fetch similar artists for original artist
            similar_artists = self.get_similar_artists(self.artist_mbid)
            #            if len(similar_artists) == 0:
            #                raise RuntimeError(f"Not enough similar artist data available for artist {self.artist_name}. Please choose a different artist.")

            # select artists
            for artist in similar_artists[start:stop]:
                artists.append({"mbid": artist["artist_mbid"]})
                if len(artists) >= self.MAX_NUM_SIMILAR_ARTISTS:
                    break

        # For all fetched artists, fetch their names
        artist_names = self.fetch_artist_names([i["mbid"] for i in artists])
        for artist in artists:
            if artist["mbid"] not in artist_names:
                raise RuntimeError("Artist %s could not be found. Is this MBID valid?" % artist["artist_mbid"])

            artist["name"] = artist_names[artist["mbid"]]

            # Store data in cache, so the post processor can create decent descriptions, title
            self.data_cache[artist["mbid"]] = artist["name"]

        # start crafting user feedback messages
        msgs = []
        if self.include_similar_artists and len(artists) == 1:
            msgs.append(f"Seed artist {artist_names[self.artist_mbid]} no similar artists.")
        else:
            if self.include_similar_artists and len(artists) < 4:
                msgs.append(f"Seed artist {artist_names[self.artist_mbid]} few similar artists.")
            msg = "artist: using seed artist %s" % artists[0]["name"]
            if self.include_similar_artists:
                msg += " and similar artists: " + ", ".join([a["name"] for a in artists[1:]])
            else:
                msg += " only"
            msgs.append(msg)

        for msg in msgs:
            self.local_storage["user_feedback"].append(msg)
        self.data_cache["element-descriptions"].append("artist %s" % artists[0]["name"])

        artist_mbids = [ artist["mbid"] for artist in artists ]
        artist_mbids = list(set(artist_mbids))
        artist_recordings = self.recording_search_by_artist.search(artist_mbids, start, stop, self.max_top_recordings_per_artist)

        # Now collect recordings from the artist and similar artists and return an interleaved
        # stream of recordings.
        for i, artist in enumerate(artists):

            # TODO: This disables top recordings caching, which needs to be re-thought given the new approach
            #if artist["mbid"] + "_top_recordings" in self.data_cache:
            #    artist["recordings"] = self.data_cache[artist["mbid"] + "_top_recordings"]
            #    continue

            recs_plist = plist(artist_recordings[artist["mbid"]])
            if len(recs_plist) < 20:
                self.local_storage["user_feedback"].append(
                    f"Artist {artist['name']} only has {'no' if len(recs_plist) == 0 else 'few'} top recordings.")

            recordings = recs_plist.random_item(start, stop, self.max_top_recordings_per_artist)

            # Now tuck away the data for caching and interleaving
            # The whole artist caching concept hasn't worked very well, and with future changes, it will likely go away.
            # For now, ignore.
            #self.data_cache[artist["mbid"] + "_top_recordings"] = recordings
            artist["recordings"] = recordings

        return interleave([a["recordings"] for a in artists])
