import sys
import urllib
from urllib.parse import quote

import requests
import ujson

from troi import Element, Release


class MSBMappingLookupElement(Element):
    '''
       Look up MBIDs for the given recordings, if possible. If recordings
       are not found, their data remains unchanged.
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/msid-mapping/json"

    def __init__(self, remove_unmatched=False):
        self.remove_unmatched = remove_unmatched

    def inputs(self):
        return [Recording]

    def outputs(self):
        return [Recording]

    def push(self, inputs):

        in_recordings = inputs[0]
        artists = ",".join([ r.artist.name for r in in_recordings ])
        recordings = ",".join([ r.name for r in in_recordings ])

        # msid-mapping/json?[msb_artist_credit_name]=portishead%2Cu2&[msb_recording_name]=strangers%2Csunday+bloody+sunday
        url = self.SERVER_URL + "?[msb_artist_credit_name]=" + quote(artists) + \
            "&[msb_recording_name]=" + quote(recordings)

        r = requests.get(url)
        if r.status_code != 200:
            r.raise_for_status()

        try:
            mappings = ujson.loads(r.text)
        except Exception as err:
            raise RuntimeError(str(err))


        entities = []
        for row in mappings:
            r = in_recordings[int(row['index'])]

            if not row['mb_artist_name']:
                if not self.remove_unmatched:
                    entities.append(r)
                continue

            if r.mbid:
                r.add_note("recording mbid %s overwritten by msb_lookup" % (r.mbid))
            r.mbid = row['mb_recording_mbid']
            r.name = row['mb_recording_name']

            if r.artist.artist_credit_id:
                r.artist.add_note("artist_credit_id %d overwritten by msb_lookup" % (r.artist.artist_credit_id))
            r.artist.artist_credit_id = row['mb_artist_credit_id']
            r.artist.name = row['mb_artist_name']

            if r.release:
                if r.release.mbid:
                    r.release.add_note("mbid %d overwritten by msb_lookup" % (r.release.mbid))
                r.release.mbid = row['mb_release_mbid']
                r.release.name = row['mb_release_name']
            else:
                r.release = Release(row['mb_release_name'], mbid=row['mb_release_mbid'])

            entities.append(r)

        self.next_elements[0].push([entities])
