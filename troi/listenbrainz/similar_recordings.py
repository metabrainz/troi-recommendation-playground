import logging

import requests

from troi import Recording, Element


class LookupSimilarRecordingsElement(Element):
    """ Lookup similar recordings.

        Given a list of recordings, this element will output recordings that are similar to the ones passed in.
    """

    def __init__(self, algorithm, count, keep_seed=False):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self.algorithm = algorithm
        self.count = count
        self.keep_seed = keep_seed

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        data = [
            {
                "recording_mbid": recording.mbid,
                "algorithm": self.algorithm
            }
            for recording in inputs[0]
        ]

        url = f"https://labs.api.listenbrainz.org/similar-recordings/json"
        # the count in this case denotes the per-item count
        # i.e. for each mbid passed to this endpoint return at most 2 similar mbids
        r = requests.post(url, json=data, params={"count": self.count})
        if r.status_code != 200:
            self.logger.info("Fetching similar recordings failed: %d. Skipping." % r.status_code)

        data = r.json()
        results = []
        if self.keep_seed:
            results.append(inputs[0][0])

        try:
            return results + [
                    Recording(mbid=item["recording_mbid"], musicbrainz={"score": item["score"]})
                for item in data[3]["data"]
            ]
        except IndexError:
            return []
