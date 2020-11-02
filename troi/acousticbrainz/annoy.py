import requests
import ujson

from troi import Element, Recording, PipelineError

"""
-> annoy similarity (timbre - similar sounding)
-> filter by similar artists (dataset name -> credit id -> similar artists)
     -> later, add in collab filtering similar artists
-> recordings from a given year/range
"""


class AnnoyLookupElement(Element):
    """
        Given an recording MBID, lookup tracks that are similar given some
        criteria (e.g. mfccs, gfccs, etc).
    """

    SERVER_URL = "http://similarity.acousticbrainz.org/api/v1/similarity/"

    def __init__(self, metric, mbid):
        """
            The given recording mbid is the source track that will be looked up 
            in the annoy index using the passed metric.
        """
        super().__init__()
        self.mbid = mbid
        self.metric = metric

    def outputs(self):
        return [Recording]

    def read(self, inputs):
        self.debug("read for %s/%s" % (self.metric, self.mbid))

        url = self.SERVER_URL + self.metric + "/" + self.mbid
        self.debug(f"url: {url}")
        r = requests.get(url, params={'remove_dups': 'true'})
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
                              'offset': row['offset']
                          }
                          )
            r.add_note("Related to %s" % self.mbid)
            entities.append(r)

        self.debug("read %d recordings" % len(entities))

        return entities
