import sys

import psycopg2
import psycopg2.extras
from psycopg2.errors import OperationalError, DuplicateTable

from troi import Entity, EntityEnum


class MBRecordingLookup(object):

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def lookup(self, recording):
        assert(recording.type == "recording")
        assert(recording.domain == "musicbrainz")

        try:
            r = recording.musicbrainz['recording']
        except KeyError:
            recording.musicbrainz['recording'] = {}
            r = recording.musicbrainz['recording']

        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory = psycopg2.extras.DictCursor) as curs:
                curs.execute('''SELECT *
                                  FROM recording
                                 WHERE gid = %s''', (recording.id,))
                row = curs.fetchone()
                if not row:
                    raise KeyError

                recording.name = row['name']
                r['artist_credit'] = row['artist_credit']
                r['recording_id'] = row['id']
                r['length'] = row['length']
                r['comment'] = row['comment']
