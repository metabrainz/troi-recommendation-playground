import requests
import ujson
from time import sleep

from troi import Element, Artist, ArtistCredit, Recording, Release, PipelineError


class MBIDMappingLookupElement(Element):
    '''
       Look up MBIDs for the given recordings, if possible. If recordings
       are not found, their data remains unchanged.

       :param remove_unmatched: If True (default False) do not return any Recordings that were not found using the mapping.
    '''

    SERVER_URL = "https://labs.api.listenbrainz.org/mbid-mapping/json"

    def __init__(self, remove_unmatched=False):
        super().__init__()
        self.remove_unmatched = remove_unmatched

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        params = []
        for r in inputs[0]:
            if r.artist_credit is not None and r.name is not None:
                params.append({"artist_credit_name": r.artist_credit.name, "recording_name": r.name})

        if not params:
            return []

        while True:
            r = requests.post(self.SERVER_URL, json=params)
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise PipelineError("Cannot fetch MBID mapping rows from ListenBrainz: HTTP code %d (%s)" % (r.status_code, r.text))

            break


        entities = []
        for row in r.json():
            r = inputs[0][int(row['index'])]

            if not row['artist_credit_name']:
                if not self.remove_unmatched:
                    entities.append(r)
                continue

            if r.mbid:
                r.add_note("recording mbid %s overwritten by mbid_lookup" % (r.mbid,))
            r.mbid = row['recording_mbid']
            r.name = row['recording_name']

            r.artist_credit = ArtistCredit(
                artist_credit_id=row['artist_credit_id'],
                name=row['artist_credit_name'],
                artists=[ Artist(mbid=mbid) for mbid in row['artist_mbids'] ] 
            )

            r.release = Release(row['release_name'], mbid=row['release_mbid'])

            entities.append(r)

        return entities
