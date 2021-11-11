import requests
import json

from troi import Element, Recording, Release, PipelineError


class MBIDMappingLookupElement(Element):
    '''
       Look up MBIDs for the given recordings, if possible. If recordings
       are not found, their data remains unchanged.
    '''

    SERVER_URL = "https://datasets.listenbrainz.org/mbid-mapping/json"

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
            params.append({"[artist_credit_name]": r.artist.name,
                           "[recording_name]": r.name})

        r = requests.post(self.SERVER_URL, json=params)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch MBID mapping rows from ListenBrainz: HTTP code %d (%s)" % (r.status_code, r.text))

        entities = []
        for row in json.loads(r.text):
            r = inputs[0][int(row['index'])]
            print(r)

            if not row['artist_credit_name']:
                if not self.remove_unmatched:
                    entities.append(r)
                continue

            if r.mbid:
                r.add_note("recording mbid %s overwritten by mbid_lookup" % (r.mbid))
            r.mbid = row['recording_mbid']
            r.name = row['recording_name']

            if r.artist.artist_credit_id:
                r.artist.add_note("artist_credit_id %d overwritten by mbid_lookup" % (r.artist.artist_credit_id))
            r.artist.artist_credit_id = row['artist_credit_id']
            r.artist.name = row['artist_credit_name']

            if r.release:
                if r.release.mbid:
                    r.release.add_note("mbid %d overwritten by mbid_lookup" % (r.release.mbid))
                r.release.mbid = row['release_mbid']
                r.release.name = row['release_name']
            else:
                r.release = Release(row['release_name'], mbid=row['release_mbid'])

            entities.append(r)

        return entities
