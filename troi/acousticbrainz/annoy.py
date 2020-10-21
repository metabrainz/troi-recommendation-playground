import sys
import urllib
from urllib.parse import quote

import requests
import ujson

from troi import Element, Recording, PipelineError


class AnnoyLookupElement(Element):
    '''
        Given an recording MBID, lookup tracks that are similar given some 
        criteria (e.g. mfccs, gfccs, etc).
    '''

    SERVER_URL = "http://similarity.acousticbrainz.org/api/v1/similarity/"

    def __init__(self, metric, mbid):
        '''
            The given recording mbid is the source track that will be looked up 
            in the annoy index using the passed metric.
        '''
        Element.__init__(self)
        self.mbid = mbid
        self.metric = metric

    def outputs(self):
        return [Recording]

    def read(self, inputs, debug=False):
        print("  annoy: read for %s/%s" % (self.metric, self.mbid))

        url = self.SERVER_URL + self.metric + "/" + self.mbid
        r = requests.get(url)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch annoy similarities from AcousticBrainz: HTTP code %d" % r.status_code)

        try:
            results = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot fetch annoy similarities from AcousticBrainz: Invalid JSON returned: " + str(err))


        entities = []
        for row in results:
            r = Recording(mbid=row['recording_mbid'], 
                          acousticbrainz={
                              'similarity': row['distance'], 
                              'offset' : row['offset']
                          }
                         )
            r.add_note("Related to %s" % self.mbid)
            entities.append(r)

        print("  annoy: read %d recordings" % len(entities))

        return entities
