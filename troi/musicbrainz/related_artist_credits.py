import copy
from collections import defaultdict
from time import sleep

import requests

from troi import Element, Recording, PipelineError, DEVELOPMENT_SERVER_URL


class RelatedArtistCreditsElement(Element):
    '''
        Look up related artist_credits, given a list of artists_credits
    '''

    SERVER_URL = DEVELOPMENT_SERVER_URL + "/artist-credit-similarity/json"

    def __init__(self, threshold=0):
        super().__init__()
        self.threshold = threshold

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        artists = inputs[0]
        ac_ids = ",".join([ str(a.artist_credit_id) for a in artists ])
        params = {"[artist_credit_id]": ac_ids,
                  "threshold": self.threshold}

        while True:
            r = requests.get(self.SERVER_URL, params=params)
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise PipelineError("Cannot fetch related artist credits from ListenBrainz: HTTP code %d" % r.status_code)

            break


        try:
            relations = r.text
        except ValueError as err:
            raise PipelineError("Cannot fetch related artist credits from ListenBrainz: Invalid JSON returned: " + str(err))

        index = defaultdict(list)
        for row in relations:
            index[row['artist_credit_id']].append(row)

        entities = []
        for artist in artists:
            a = copy.deepcopy(artist)
            a.mb['related_artist_credit_ids'] = index[artist.artist_credit_id]
            entities.append(a)

        return entities
