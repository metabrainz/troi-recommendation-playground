import requests
import ujson

from troi import Element, Recording, PipelineError

"""
-> annoy similarity (timbre - similar sounding)
-> filter by similar artists (dataset name -> credit id -> similar artists)
     -> later, add in collab filtering similar artists
-> recordings from a given year/range
"""

VALID_METRICS = ['mfccs', 'mfccsw', 'gfccs', 'gfccsw', 'key', 'bpm', 'onsetrate', 'moods',
                 'instruments', 'dortmund', 'rosamerica', 'tzanetakis']


class AnnoyLookupElement(Element):
    """
        Given an recording MBID, lookup tracks that are similar given some
        criteria (e.g. mfccs, gfccs, etc).
    """

    SERVER_URL = "https://acousticbrainz.org/api/v1/similarity/"

    def __init__(self, metric, mbid):
        """
            The given recording mbid is the source track that will be looked up 
            in the annoy index using the passed metric.
        """
        super().__init__()
        self.mbid = mbid

        if metric.lower() not in VALID_METRICS:
            raise PipelineError("metric %s is not valid. Must be one of %s" % (metric, '.'.join(VALID_METRICS)))
        self.metric = metric

    def outputs(self):
        return [Recording]

    def read(self, inputs):
        self.debug("read for %s/%s" % (self.metric, self.mbid))

        url = self.SERVER_URL + self.metric + "/"
        self.debug(f"url: {url}")
        # recording_ids format is mbid:offset;mbid:offset
        r = requests.get(url, params={'remove_dups': 'all',
                                      'recording_ids': self.mbid + ":0",
                                      'n_neighbours': 500})
        if r.status_code != 200:
            raise PipelineError("Cannot fetch annoy similarities from AcousticBrainz: HTTP code %d" % r.status_code)

        try:
            results = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot fetch annoy similarities from AcousticBrainz: Invalid JSON returned: " + str(err))

        entities = []
        for row in results[self.mbid]["0"]:
            r = Recording(mbid=row['recording_mbid'], 
                          acousticbrainz={
                              'metric': self.metric,
                              'similarity_from': self.mbid,
                              'similarity': row['distance'], 
                              'offset': row['offset']
                          }
                          )
            r.add_note("Related to %s with metric %s" % (self.mbid, self.metric))
            entities.append(r)

        self.debug("read %d recordings" % len(entities))

        return entities
