from abc import abstractmethod

import requests

from troi import Recording, Artist
from troi.service import Service
from troi.splitter import plist

# NOTES FOR LB API improvements:
# Tags:
#    - flatten tag data for simplicity
#    - use series of tighter random spots to speed up or searches for popular tags
# Artist:
#    - Support percent based popular track lookups and move logic to server


class RecordingSearchByTagService(Service):

    SLUG = "recording-search-by-tag"

    def __init__(self):
        super().__init__(self.SLUG)

    def search(self, tags, operator, begin_percent, end_percent, num_recordings):
        """
            Fetch the tag data from the LB API and return it as a dict.
        """

        data = {
            "condition": operator,
            "count": num_recordings,
            "begin_percent": begin_percent,
            "end_percent": end_percent,
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

    def search(self, artists, begin_percent, end_percent, num_recordings):
        """
            Fetch the artist data from the LB API and return it as a dict.

            NOTE: This search is poor -- it should span all recordings by an artist not, just the top ones!
        """

        artists_recordings = {}
        for artist_mbid in artists:
            params={"artist_mbid": artist_mbid}
            r = requests.get("https://api.listenbrainz.org/1/popularity/top-recordings-for-artist", params={"artist_mbid": artist_mbid})
            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch top artist recordings: {r.status_code} ({r.text})")

            recordings = plist()
            for recording in r.json():
                artist = Artist(mbids=recording["artist_mbids"], name=recording["artist_name"])
                recordings.append(
                    Recording(mbid=recording["recording_mbid"],
                              name=recording["recording_name"],
                              duration=recording["length"],
                              artist=artist))

            artists_recordings[artist_mbid] = recordings.random_item(begin_percent, end_percent, num_recordings)

        return artists_recordings
