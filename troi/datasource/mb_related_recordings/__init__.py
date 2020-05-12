import sys

import psycopg2
import psycopg2.extras

from troi.datasource import DataSource
from troi.lookup.mb_recording import MBRecordingLookup
from troi import Entity, EntityEnum


class MBRelatedRecordingsDataSource(DataSource):
    '''
        Fetch related recordings -- this data source is more for demo purposes than actual good results.
    '''

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def get(self, recording, threshold=1, max_items=100):

        # If we only have an mbid, look up the id and load the rest of the metadata
        if 'recording_id' not in recording.musicbrainz:
            MBRecordingLookup(self.db_connect).lookup(recording)

        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:

                curs.execute("""SELECT count,
                                       rrr.recording_0 AS recording_0_id,
                                       a0.gid AS recording_0_mbid,
                                       a0.name AS recording_0_name,
                                       rrr.recording_1 as recording_1_id,
                                       a1.gid AS recording_1_mbid,
                                       a1.name AS recording_1_name
                                  FROM recording_recording_relations rrr
                                  JOIN recording a0 ON rrr.recording_0 = a0.id
                                  JOIN recording a1 ON rrr.recording_1 = a1.id
                                 WHERE (rrr.recording_0 = %s OR rrr.recording_1 = %s) AND
                                       count >= %s
                              ORDER BY count desc
                                 LIMIT %s""", (recording.musicbrainz['recording']['recording_id'],
                                               recording.musicbrainz['recording']['recording_id'],
                                               threshold,
                                               max_items))

                relations = []
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    if recording.musicbrainz['recording']['recording_id'] == row['recording_1_id']:
                        e = Entity(EntityEnum("recording"),
                                   row['recording_0_mbid'],
                                   row['recording_0_name'],
                                   {
                                       'musicbrainz' : {
                                           'artist' : {},
                                           'release' : {},
                                           'recording' : {
                                               'recording_id' : row['recording_0_id'],
                                               'recording_relations_count' : row['count']
                                           }
                                       }
                                   })
                    else:
                        e = Entity(EntityEnum("recording"),
                                   row['recording_1_mbid'],
                                   row['recording_1_name'],
                                   {
                                       'musicbrainz' : {
                                           'artist' : {},
                                           'release' : {},
                                           'recording' : {
                                               'recording_id' : row['recording_1_id'],
                                               'recording_relations_count' : row['count']
                                           }
                                       }
                                   })

                    relations.append(e)

                return relations
