from abc import abstractmethod

import requests

from troi import Recording, Artist
from troi.service import Service
from troi.splitter import plist

# NOTES FOR LB API improvements:
# Tags:
#    - flatten tag data for simplicity
#    - use series of tighter random spots to speed up or searches for popular tags


class RecordingSearchByTagService(Service):

    SLUG = "recording-search-by-tag"

    def __init__(self):
        super().__init__(self.SLUG)

    def search(self, tags, operator, pop_begin, pop_end, num_recordings):
        """
            Fetch the tag data from the LB API and return it as a dict.
        """

        data = {
            "condition": operator,
            "count": num_recordings,
            "begin_percent": pop_begin,
            "end_percent": pop_end,
            "tag": tags,
            "min_tag_count": 1
        }
        r = requests.get("https://api.listenbrainz.org/1/lb-radio/tags", params=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch recordings for tags. {r.text}")

        recordings = []
        for rec in self.flatten_tag_data(dict(r.json())):
            recordings.append(Recording(mbid=rec["recording_mbid"]))

        return plist(recordings)

    def flatten_tag_data(self, tag_data):

        flat_data = list(tag_data["recording"])
        flat_data.extend(list(tag_data["release-group"]))
        flat_data.extend(list(tag_data["artist"]))

        return sorted(flat_data, key=lambda f: f["percent"], reverse=True)


class RecordingSearchByArtistService(Service):

    SLUG = "recording-search-by-artist"

    def __init__(self):
        super().__init__(self.SLUG)

    def search(self, mode, artist_mbid, pop_begin, pop_end, max_recordings_per_artist, max_similar_artists):
        """
            Given a seed artist mbid, find and select similar artists (via LB similar artists data).

            pop_begin: The lower bound on recording popularity
            pop_end: The upper bound on recording popularity
            max_recordings_per_artist: The number of recordings to collect for each artist.
            max_similar_artists: The maximum number of similar artists to select.
        """

        params = {
                "mode": mode,
                "max_similar_artists": max_similar_artists,
                "max_recordings_per_artist": max_recordings_per_artist,
                "pop_begin": pop_begin,
                "pop_end": pop_end
        }
        url = f"https://api.listenbrainz.org/1/lb-radio/artist/{artist_mbid}"

        r = requests.get(url, params=params)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch lb_radio artists: {r.status_code} ({r.text})")

        try:
            artists = r.json()
        except IndexError:
            return []

        for artist_mbid in artists:
            recordings = artists[artist_mbid]
            updated = []
            for rec in recordings:
                updated.append(Recording(mbid=rec["recording_mbid"], musicbrainz={"total_listen_count": rec["total_listen_count"]}))
            artists[artist_mbid] = updated

        return artists
