import sys
import uuid

import psycopg2
import psycopg2.extras

from troi import Entity, EntityEnum

psycopg2.extras.register_uuid()

class MBRecordingLookup():
    '''
        Look up a musicbrainz recording
    '''

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def lookup(self, recording_arg):
        '''
            Given an entity or a list of entities, lookup the basic metadata for each of the items
        '''

        if type(recording_arg) == list:
            recordings = recording_arg
        elif isinstance(recording_arg, Entity):
            recordings = [ recording_arg ]
        else:
            raise TypeError("argument to lookup must be recording Entity or list of recording Entities")

        for recording in recordings:
            assert recording.domain == "musicbrainz"
            assert isinstance(recording.id, uuid.UUID)
            if recording.type != EntityEnum("recording"):
                raise TypeError("one of the given entities is not of type recording.")

        mbid_index = {}
        for i, r in enumerate(recordings):
            mbid_index[r.id] = i


        with psycopg2.connect(self.db_connect) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                mbids = tuple([ psycopg2.extensions.adapt(r.id) for r in recordings ])
                curs.execute('''SELECT r.gid AS gid, r.id AS recording_id, r.name AS recording_name, length, comment, 
                                       ac.id AS artist_credit_id, ac.name AS artist_credit_name
                                  FROM recording r
                                  JOIN artist_credit ac ON r.artist_credit = ac.id
                                 WHERE gid IN %s''', (mbids,))
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    r = recordings[mbid_index[row['gid']]]
                    r.name = row['recording_name']

                    r.mb_recording['artist_credit'] = row['artist_credit_id']
                    r.mb_recording['recording_id'] = row['recording_id']
                    r.mb_recording['length'] = row['length']
                    r.mb_recording['comment'] = row['comment']
                    r.mb_artist['artist_credit_id'] = row['artist_credit_id']
                    r.mb_artist['artist_credit_name'] = row['artist_credit_name']
