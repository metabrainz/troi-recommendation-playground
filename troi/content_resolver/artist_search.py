import os
from collections import defaultdict
import datetime
import sys
from time import sleep

import peewee
import requests

from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording, RecordingMetadata
from troi.content_resolver.utils import select_recordings_on_popularity
from troi.recording_search_service import RecordingSearchByArtistService
from troi.plist import plist

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

class LocalRecordingSearchByArtistService(RecordingSearchByArtistService):
    '''
    Given the local database, search for artists that meet given tag criteria
    '''

    def __init__(self):
        RecordingSearchByArtistService.__init__(self)

    def get_similar_artists(self, artist_mbid):
        """ Fetch similar artists, given an artist_mbid. Returns a sored plist of artists. """

        while True:
            r = requests.post("https://labs.api.listenbrainz.org/similar-artists/json",
                              json=[{
                                  'artist_mbids':
                                  [artist_mbid],
                                  'algorithm':
                                  "session_based_days_7500_session_300_contribution_5_threshold_10_limit_100_filter_True_skip_30"
                              }])
            if r.status_code == 429:
                sleep(2)
                continue
            if r.status_code != 200:
                raise RuntimeError(f"Cannot fetch similar artists: {r.status_code} ({r.text})")

            break

        artists = r.json()

        # Knock down super hyped artists
        for artist in artists:
            if artist["artist_mbid"] in OVERHYPED_SIMILAR_ARTISTS:
                artist["score"] /= 3  # Chop!

        return plist(sorted(artists, key=lambda a: a["score"], reverse=True))

    def search(self, mode, artist_mbid, pop_begin, pop_end, max_recordings_per_artist, max_similar_artists):

        """
        Perform an artist search. Parameters:

        mode: the mode used for this artist search
        pop_begin: if many recordings match the above parameters, return only
                       recordings that have a minimum popularity percent score
                       of pop_begin.
        pop_end: if many recordings match the above parameters, return only
                     recordings that have a maximum popularity percent score
                     of pop_end.
        max_recordings_per_artist: The number of recordings to collect for each artist.
        max_similar_artists: The maximum number of similar artists to select.

        If only few recordings match, the pop_begin and pop_end are ignored.
        """

        similar_artists = self.get_similar_artists(artist_mbid)
        query = """SELECT popularity
                        , recording_mbid
                        , artist_mbid
                        , file_id
                        , file_id_type
                     FROM recording
                     JOIN recording_metadata
                       ON recording.id = recording_metadata.recording_id
                    WHERE artist_mbid in (%s)
                 ORDER BY artist_mbid
                        , popularity"""

        artist_mbids = [artist["artist_mbid"] for artist in similar_artists]
        placeholders = ",".join(("?", ) * len(similar_artists))
        cursor = db.execute_sql(query % placeholders, params=artist_mbids)

        artists = defaultdict(list)
        for rec in cursor.fetchall():
            artists[rec[2]].append({
                "popularity": rec[0],
                "recording_mbid": rec[1],
                "artist_mbid": rec[2],
                "file_id": rec[3],
                "file_id_type": rec[4]
            })

        for artist in artists:
            artists[artist] = select_recordings_on_popularity(artists[artist], pop_begin, pop_end, max_recordings_per_artist)

        return artists, []
