import sys

import psycopg2
import psycopg2.extras

from troi import Entity, EntityEnum


class MBArtistCreditLookup():
    '''
        Lookup musicbrainz artist_credits.
    '''

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def lookup(self, artist_credit):
        assert artist_credit.type == EntityEnum("artist-credit")
        assert artist_credit.domain == "musicbrainz"

        ac = artist_credit.musicbrainz['artist']
        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                curs.execute('''SELECT *
                                  FROM artist_credit
                                 WHERE id = %s''', (artist_credit.id,))
                row = curs.fetchone()
                if not row:
                    raise KeyError

                artist_credit.name = row['name']
                ac['artist_credit_id'] = row['id']
