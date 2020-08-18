import sys
import uuid
from urllib.parse import quote

import psycopg2
import psycopg2.extras
import requests
import ujson

from troi import Element, Artist, Recording

psycopg2.extras.register_uuid()

class RecordingLookupElement(Element):
    '''
        Look up a musicbrainz data for a list of recordings, based on MBID. 
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/recording-mbid-lookup/json"

    def inputs(self):
        return [ Recording ]

    def outputs(self):
        return [ Recording ]

    def read(self, inputs):

        recordings = inputs[0]
        if not recordings:
            return []

        data = []
        r_mbids = ",".join([ r.mbid for r in recordings ])
        for r in recordings:
            data.append({ 'recording_mbid': r.mbid })
        r = requests.post(self.SERVER_URL, json=data)
        if r.status_code != 200:
            r.raise_for_status()

        try:
            rows = ujson.loads(r.text)
        except Exception as err:
            raise RuntimeError(str(err))

        mbid_index = {}
        for row in rows:
            mbid_index[row['recording_mbid']] = row

        for r in recordings:
            if mbid_index.get(r.mbid) == None:
                continue
            row = mbid_index[r.mbid]
            if not r.artist:
                a = Artist(name=row['artist_credit_name'],
                           mbids=row['[artist_credit_mbids]'],
                           artist_credit_id=row['artist_credit_id'])
                r.artist = a
            else:
                r.artist.name = row['artist_credit_name']
                r.artist.mbids = row['artist_credit_mbids']
                r.artist.artist_credit_id = row['artist_credit_id']

            r.name = row['recording_name']
            r.length = row['length']

        print("  MB recording lookup: read %d recordings" % len(recordings))

        return recordings
