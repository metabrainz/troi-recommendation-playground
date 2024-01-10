import requests
import ujson

from troi import Element, Artist, PipelineError, DEVELOPMENT_SERVER_URL


class ArtistCreditIdLookupElement(Element):
    '''
       Look up artist_credit_name and artist_credit_mbids for the Artists that have artist_credit_id defined.

       No parameters needed for objection creation.

    '''

    SERVER_URL = DEVELOPMENT_SERVER_URL + "/artist-credit-id-lookup/json"

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
