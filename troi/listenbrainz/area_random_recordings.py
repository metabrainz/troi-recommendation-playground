import sys
import uuid
from urllib.parse import quote

import requests
import ujson

from troi import Element, Artist, Recording, PipelineError

class AreaRandomRecordingsElement(Element):
    '''
        Given an area, find random tracks from releases that were released
        by artists from that given area.
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/area-random-recordings/json"

    def __init__(self, area_id, start_year=0, end_year=3000):
        Element.__init__(self)
        self.area_id = area_id
        self.start_year = start_year
        self.end_year = end_year

    @staticmethod
    def inputs():
        return [ ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs, debug=False):

        data = [ { 'area_id': self.area_id, 'start_year' : self.start_year, 'end_year' : self.end_year } ]
        r = requests.post(self.SERVER_URL, json=data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch area random recordings from ListenBrainz. HTTP code %s" % r.status_code)

        try:
            rows = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot fetch area random recordings from ListenBrainz. Invalid JSON returned: " + str(err))

        recordings = []
        for row in rows:
            recordings.append(Recording(mbid=row['recording_mbid'], 
                                        name=row['recording_name'], 
                                        year=row['year'],
                                        artist=Artist(name=row['artist_credit_name'],
                                                      artist_credit_id=row['artist_credit_id'])))

        return recordings
