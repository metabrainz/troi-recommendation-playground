import sys

import psycopg2
import psycopg2.extras
from psycopg2.errors import OperationalError, DuplicateTable

from troi.datasource import DataSource
from troi.lookup.mb_artist import MBArtistLookup
from troi import Entity, EntityEnum


class MBRelatedArtistsDataSource(DataSource):

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def get(self, artist, threshold = 1, max_items = 100):

        # If we only have an mbid, look up the id and load the rest of the metadata
        if 'artist_id' not in artist.musicbrainz:
            MBArtistLookup(self.db_connect).lookup(artist)

        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory = psycopg2.extras.DictCursor) as curs:

                curs.execute("""SELECT count, 
                                       arr.artist_0 AS artist_0_id, 
                                       a0.gid AS artist_0_mbid, 
                                       a0.name AS artist_0_name, 
                                       arr.artist_1 as artist_1_id,
                                       a1.gid AS artist_1_mbid, 
                                       a1.name AS artist_1_name 
                                  FROM artist_artist_relations arr
                                  JOIN artist a0 ON arr.artist_0 = a0.id
                                  JOIN artist a1 ON arr.artist_1 = a1.id
                                 WHERE (arr.artist_0 = %s OR arr.artist_1 = %s)
                                   AND count >= %s
                              ORDER BY count desc
                                 LIMIT %s""", (artist.musicbrainz['artist']['artist_id'], 
                                               artist.musicbrainz['artist']['artist_id'],
                                               threshold,
                                               max_items))

                relations = []
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    if artist.musicbrainz['artist']['artist_id'] == row['artist_1_id']: 
                        e = Entity(EntityEnum("artist"),
                            row['artist_0_mbid'], 
                            row['artist_0_name'],
                            { 
                                'musicbrainz' : { 
                                    'artist' : {
                                        'artist_id ' : row['artist_0_id'],
                                        'artist_relations_count' : row['count'] 
                                    }
                                }
                            })
                    else:
                        e = Entity(EntityEnum("artist"),
                            row['artist_1_mbid'], 
                            row['artist_1_name'],
                            { 
                                'musicbrainz' : { 
                                    'artist' : {
                                        'artist_id ' : row['artist_1_id'],
                                        'artist_relations_count' : row['count'] 
                                    }
                                }
                            })

                    relations.append(e)

                return relations
