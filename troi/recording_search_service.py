from abc import abstractmethod
from time import sleep

import requests

from troi import Recording, Artist, ArtistCredit
from troi.service import Service
from troi.plist import plist


class RecordingSearchByTagService(Service):

    SLUG = "recording-search-by-tag"

    def __init__(self):
        super().__init__(self.SLUG)

    def search(self, tags, operator, pop_begin, pop_end, num_recordings):
        """
            Fetch the tag data from the LB API and return it as a dict.
        """

        data = {
            "operator": operator,
            "count": num_recordings,
            "pop_begin": pop_begin,
            "pop_end": pop_end,
            "tag": tags
        }
        while True:
            r = requests.get("https://api.listenbrainz.org/1/lb-radio/tags", params=data)
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch recordings for tags. {r.text}")

            break


        return plist([ Recording(mbid=rec["recording_mbid"], musicbrainz={"popularity": rec["percent"]}) for rec in r.json() ])


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

        while True:
            r = requests.get(url, params=params)
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch lb_radio artists: {r.status_code} ({r.text})")

            break


        try:
            artists = r.json()
        except IndexError:
            return {}, []

        artist_recordings = {}
        msgs = []
        for artist_mbid in artists:
            recordings = plist()
            for recording in artists[artist_mbid]:
                artist_credit = ArtistCredit(artists=[Artist(mbid=recording["similar_artist_mbid"])],
                                             name=recording["similar_artist_name"])
                recordings.append(Recording(mbid=recording["recording_mbid"],
                                            artist_credit=artist_credit,
                                            musicbrainz={"total_listen_count": recording["total_listen_count"]}))

            # Below is a hack, since the endpoint seems to return one track too few
            if len(recordings) < max_recordings_per_artist - 1:
                msgs.append("Artist %s has only few top recordings in %s mode" % (recordings[0].artist_credit.name, mode))

            artist_recordings[artist_mbid] = recordings.random_item(pop_begin, pop_end, max_recordings_per_artist)

        return artist_recordings, msgs
