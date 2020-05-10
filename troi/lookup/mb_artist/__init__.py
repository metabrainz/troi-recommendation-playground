import sys

import psycopg2
import psycopg2.extras
from psycopg2.errors import OperationalError, DuplicateTable

from troi import Entity, EntityEnum


class MBArtistLookup(object):

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def lookup(self, artist):
        assert(artist.type == "artist")
        assert(artist.domain == "musicbrainz")

        a = artist.musicbrainz['artist']
        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory = psycopg2.extras.DictCursor) as curs:
                curs.execute('''SELECT *
                                  FROM artist
                                 WHERE gid = %s''', (artist.id,))
                row = curs.fetchone()
                if not row:
                    raise KeyError

                artist.name = row['name']
                a['artist_id'] = row['id']
                a['sort_name'] = row['sort_name']
                a['type'] = row['type']
                a['gender'] = row['gender']
                a['comment'] = row['comment']
