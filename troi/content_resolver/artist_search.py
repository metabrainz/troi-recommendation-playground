import os
from collections import defaultdict
import datetime
import sys

import peewee
import requests

from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording, RecordingMetadata
from troi.content_resolver.utils import select_recordings_on_popularity
from troi.recording_search_service import RecordingSearchByArtistService
from troi.splitter import plist


class LocalRecordingSearchByArtistService(RecordingSearchByArtistService):
    '''
    Given the local database, search for artists that meet given tag criteria
    '''

    def __init__(self):
        RecordingSearchByArtistService.__init__(self)

    def search(self, artist_mbids, begin_percent, end_percent, num_recordings):
        """
        Perform an artist search. Parameters:

        tags - a list of artist_mbids for which to search recordings
        begin_percent - if many recordings match the above parameters, return only
                        recordings that have a minimum popularity percent score
                        of begin_percent.
        end_percent - if many recordings match the above parameters, return only
                      recordings that have a maximum popularity percent score
                      of end_percent.
        num_recordings - ideally return these many recordings

        If only few recordings match, the begin_percent and end_percent are
        ignored.
        """

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

        placeholders = ",".join(("?", ) * len(artist_mbids))
        cursor = db.execute_sql(query % placeholders, params=tuple(artist_mbids))

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
            artists[artist] = select_recordings_on_popularity(artists[artist], begin_percent, end_percent, num_recordings)

        return artists
