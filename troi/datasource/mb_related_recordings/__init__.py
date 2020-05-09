import sys

import psycopg2
import psycopg2.extras
from psycopg2.errors import OperationalError, DuplicateTable

from troi.datasource import DataSource
from troi import Entity


class MBRelatedArtistsDataSource(DataSource):

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def get(self, artist_mbid, threshold = 2, max_items = 100):

        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory = psycopg2.extras.DictCursor) as curs:
                curs.execute('''SELECT id
                                  FROM artist
                                 WHERE gid = %s''', (artist_mbid,))
                artist_row = curs.fetchone()
                if not row:
                    raise KeyError

                artist_id = artist_row[0]
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
                                   AND count > 2
                              ORDER BY count desc""", (artist_id, artist_id))

                relations = []
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    if artist_id == row['artist_1_id']: 
                        e = Entity("musicbrainz", 
                            row['artist_0_mbid], 
                            MusicBrainzEntityType("artist"), { 
                                'musicbrainz' : { 
                                    'artist_name ' : row['artist_0_name'],
                                    'artist_id ' : row['artist_0_id'],
                                    'artist_relations_count' : row['count'] 
                                }
                            })
                    else:
                        e = Entity("musicbrainz", 
                            row['artist_1_mbid], 
                            MusicBrainzEntityType("artist"), { 
                                'musicbrainz' : { 
                                    'artist_name ' : row['artist_1_name'],
                                    'artist_id ' : row['artist_1_id'],
                                    'artist_relations_count' : row['count'] 
                                }
                            })

                    relations.append(e)

                return relations
