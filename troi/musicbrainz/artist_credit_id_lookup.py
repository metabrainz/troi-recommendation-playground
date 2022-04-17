import requests
import ujson

from troi import Element, Artist, PipelineError


class ArtistCreditIdLookupElement(Element):
    '''
       Look up MBIDs for the given artist_credit_ids
    '''

    SERVER_URL = "http://wolf.metabrainz.org:8000/artist-credit-id-lookup/json"

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [Artist]

    @staticmethod
    def outputs():
        return [Artist]

    def read(self, inputs):

        ac_ids = []
        index = {}
        for a in inputs[0]:
            ac_ids.append(str(a.artist_credit_id))
            index[a.artist_credit_id] = a

        params = {"[artist_credit_id]": ",".join(ac_ids)}
        r = requests.get(self.SERVER_URL, params=params)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch artist credits from ListenBrainz: HTTP code %d" % r.status_code)

        try:
            artists = ujson.loads(r.text)
        except Exception as err:
            raise PipelineError("Cannot fetch artist credits from ListenBrainz: Invalid JSON returned: " + str(err))

        entities = []
        for row in artists:
            a = index[row['artist_credit_id']]
            a.name = row['artist_credit_name']
            a.mbids = row['artist_credit_mbids']
            entities.append(a)

        return entities
