import sys

import psycopg2
import psycopg2.extras

from troi.datasource import DataSource
from troi.lookup.mb_artist_credit import MBArtistCreditLookup
from troi import Entity, EntityEnum


class MBRelatedArtistCreditsDataSource(DataSource):
    '''
        Lookup related artist credits
    '''

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def get(self, artist_credit, threshold=1, max_items=100):

        # If we only have an mbid, look up the id and load the rest of the metadata
        if 'artist_id' not in artist_credit.musicbrainz:
            MBArtistCreditLookup(self.db_connect).lookup(artist_credit)

        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:

                curs.execute("""SELECT count,
                                       arr.artist_credit_0 AS artist_credit_0_id,
                                       a0.id AS artist_0_id,
                                       a0.gid AS artist_0_mbid,
                                       a0.name AS artist_0_name,
                                       arr.artist_credit_1 as artist_credit_1_id,
                                       a1.id AS artist_1_id,
                                       a1.gid AS artist_1_mbid,
                                       a1.name AS artist_1_name
                                  FROM artist_credit_artist_credit_relations arr
                                  JOIN artist a0 ON arr.artist_credit_0 = a0.id
                                  JOIN artist a1 ON arr.artist_credit_1 = a1.id
                                 WHERE (arr.artist_credit_0 = %s OR arr.artist_credit_1 = %s)
                                   AND count >= %s
                              ORDER BY count desc
                                 LIMIT %s""", (artist_credit.musicbrainz['artist']['artist_credit_id'],
                                               artist_credit.musicbrainz['artist']['artist_credit_id'],
                                               threshold,
                                               max_items))

                relations = []
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    if artist_credit.musicbrainz['artist']['artist_credit_id'] == row['artist_credit_1_id']:
                        e = Entity(EntityEnum("artist-credit"),
                                   row['artist_credit_0_id'],
                                   "",
                                   {
                                       'musicbrainz' : {
                                           'artist' : {
                                               'artist_id' : row['artist_0_id'],
                                               'artist_credit_id' : row['artist_credit_0_id'],
                                               'artist_mbid' : row['artist_0_mbid'],
                                               'artist_name' : row['artist_0_name'],
                                               'artist_credit_relations_count' : row['count']
                                           }
                                       }
                                   })
                    else:
                        e = Entity(EntityEnum("artist-credit"),
                                   row['artist_credit_1_id'],
                                   "",
                                   {
                                       'musicbrainz' : {
                                           'artist' : {
                                               'artist_id' : row['artist_1_id'],
                                               'artist_credit_id' : row['artist_credit_1_id'],
                                               'artist_mbid' : row['artist_1_mbid'],
                                               'artist_name' : row['artist_1_name'],
                                               'artist_credit_relations_count' : row['count']
                                           }
                                       }
                                   })

                    relations.append(e)

                return relations
