import sys
import urllib
import copy
from collections import defaultdict
from urllib.parse import quote

import requests
import ujson

from troi import Element, Release, PipelineError


class RelatedArtistCreditsElement(Element):
    '''
        Look up related artist_credits, given a list of artists_credits
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/artist-credit-similarity/json"

    def __init__(self, threshold=0):
        self.threshold = threshold

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs, debug=False):

        artists = inputs[0]
        ac_ids = ",".join([ str(a.artist_credit_id) for a in artists ])
        url = self.SERVER_URL + "?[artist_credit_id]=" + quote(ac_ids) + \
            "&threshold=%d" % self.threshold

        r = requests.get(url)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch related artist credits from ListenBrainz: HTTP code %d" % r.status_code)

        try:
            relations = ujson.loads(r.text)
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
