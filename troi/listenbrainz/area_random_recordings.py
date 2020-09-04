import sys
import uuid
from urllib.parse import quote

import psycopg2
import psycopg2.extras
import requests
import ujson

from troi import Element, Artist, Recording

psycopg2.extras.register_uuid()

class AreaRandomTracksElement(Element):
    '''
        Given an area, find random tracks from releases that were released
        by artists from that given area.
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/area-random-recordings/json"

    def __init__(self, area_id):
        Element.__init__(self)
        self.area_id = area_id

    def inputs(self):
        return [ ]

    def outputs(self):
        return [ Recording ]

    def read(self, inputs):

        data = [ { 'area_id': self.area_id, 'start_year' : '0', 'end_year' : '3000' } ]
        r = requests.post(self.SERVER_URL, json=data)
        if r.status_code != 200:
            r.raise_for_status()

        try:
            rows = ujson.loads(r.text)
        except Exception as err:
            raise RuntimeError(str(err))

        recordings = []
        for row in rows:
            recordings.append(Recording(mbid=row['recording_mbid'], 
                                        name=row['recording_name'], 
                                        artist=Artist(name=row['artist_credit_name'],
                                                      artist_credit_id=row['artist_credit_id'])))

        print("   country random recording: read %d recordings" % len(recordings))

        return recordings
