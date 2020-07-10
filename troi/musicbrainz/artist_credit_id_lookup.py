import sys
import urllib
from urllib.parse import quote

import requests
import ujson

from troi import Element, Artist


class ArtistCreditIdLookupElement(Element):
    '''
       Look up MBIDs for the given artist_credit_ids
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/artist-credit-id-lookup/json"

    def __init__(self):
        pass

    def inputs(self):
        return [Artist]

    def outputs(self):
        return [Artist]

    def read(self, inputs):

        ac_ids = []
        index = {}
        for a in inputs[0]:
            ac_ids.append(str(a.artist_credit_id))
            index[a.artist_credit_id] = a

        url = self.SERVER_URL + "?[artist_credit_id]=" + quote(",".join(ac_ids))

        r = requests.get(url)
        if r.status_code != 200:
            r.raise_for_status()

        try:
            artists = ujson.loads(r.text)
        except Exception as err:
            raise RuntimeError(str(err))

        entities = []
        for row in artists:
            a = index[row['artist_credit_id']]
            a.name = row['artist_credit_name']
            a.mbids = row['artist_credit_mbids']
            entities.append(a)

        return entities
