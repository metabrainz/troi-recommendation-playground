import requests
import ujson

from troi import Element, Artist, Recording, PipelineError, DEVELOPMENT_SERVER_URL

class AreaRandomRecordingsElement(Element):
    '''
        Given an area, find random Recordings from releases that were released by artists from that given area.

        :param area_id: A musicbrainz area_id (integer)
        :param start_year: The start year of the year range.
        :param end_year: The end year of the year range.
    '''

    SERVER_URL =  DEVELOPMENT_SERVER_URL + "/area-random-recordings/json"

    def __init__(self, area_id, start_year=0, end_year=3000):
        super().__init__()
        self.area_id = area_id
        self.start_year = start_year
        self.end_year = end_year

    @staticmethod
    def inputs():
        return [ ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs):

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
