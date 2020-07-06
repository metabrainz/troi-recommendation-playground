import sys
import uuid

import psycopg2
import psycopg2.extras

from troi import Element, Artist, Recording

psycopg2.extras.register_uuid()

class RecordingLookupElement(Element):
    '''
        Look up a musicbrainz data for a list of recordings, based on MBID. 
    '''

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string

    def inputs(self):
        return [ Recording ]

    def outputs(self):
        return [ Recording ]

    def push(self, inputs):

        recordings = inputs[0]

        mbid_index = {}
        for i, r in enumerate(recordings):
            mbid_index[r.mbid] = i

        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                mbids = tuple([ psycopg2.extensions.adapt(r.mbid) for r in recordings ])
                curs.execute('''SELECT r.gid AS gid, r.id AS recording_id, r.name AS recording_name, r.length, r.comment, 
                                       ac.id AS artist_credit_id, ac.name AS artist_credit_name, 
                                       array_agg(r.gid) AS artist_mbids
                                  FROM recording r
                                  JOIN artist_credit ac 
                                    ON r.artist_credit = ac.id
                                  JOIN artist_credit_name acn
                                    ON ac.id = acn.artist_credit
                                  JOIN artist a
                                    ON acn.artist = a.id
                                 WHERE r.gid 
                                    IN %s
                              GROUP BY r.gid, r.id, r.name, r.length, r.comment, ac.id, ac.name''', (mbids,))

                output = []
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    a = Artist(name=row['artist_credit_name'],
                               mbids=row['artist_mbids'],
                               artist_credit_id=row['artist_credit_id'])
                    r = Recording(row['recording_name'], str(row['gid']), length=row['length'], artist=a)
                    output.append(r)

        self.next_elements[0].push([output])
