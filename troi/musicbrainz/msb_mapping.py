import sys
import urllib
from urllib.parse import quote

import requests
import ujson

from troi.datafilter import DataFilter
from troi import Entity, EntityEnum



class MSBMappingFilter(DataFilter):
    '''
       Look up MBIDs for the given recordings, if possible. If recordings
       are not found, their data remains unchanged.
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/msid-mapping/json"

    def __init__(self):
        pass


    def filter(self, recordings): 

        artists = ",".join([ r.mb_artist['artist_credit_name'] for r in recordings ])
        recordings = ",".join([ r.mb_recording['recording_name'] for r in recordings ])

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
            entities.append(Entity(EntityEnum("recording"),
               row['mb_recording_mbid'],
               row['mb_recording_name'],
               {
                   'musicbrainz' : {
                       'artist' : {
                           'artist_credit_id ': row['mb_recording_mbid'],
                           'artist_credit_name': row['mb_artist_name']
                       },
                       'release' : {
                           'release_mbid ': row['mb_release_mbid'],
                           'release_name': row['mb_release_name']
                       }
                   }
               }))

        return entities
