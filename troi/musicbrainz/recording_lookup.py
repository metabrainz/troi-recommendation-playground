import sys
import uuid
from urllib.parse import quote

import requests
import ujson

from troi import Element, Artist, Recording

class RecordingLookupElement(Element):
    '''
        Look up a musicbrainz data for a list of recordings, based on MBID. 
    '''

    SERVER_URL = "https://labs.api.listenbrainz.org/recording-mbid-lookup/json?count=%d"

    @staticmethod
    def inputs():
        return [ Recording ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs, debug=False):

        recordings = inputs[0]
        if not recordings:
            return []

        data = []
        r_mbids = ",".join([ r.mbid for r in recordings ])
        for r in recordings:
            data.append({ '[recording_mbid]': r.mbid })

        if debug:
            print("- debug %d recordings" % len(recordings))

        r = requests.post(self.SERVER_URL % len(recordings), json=data)
        if r.status_code != 200:
            r.raise_for_status()

        try:
            rows = ujson.loads(r.text)
            if debug:
                print("- debug %d rows in response" % len(rows))
        except Exception as err:
            raise RuntimeError(str(err))

        mbid_index = {}
        for row in rows:
            mbid_index[row['original_recording_mbid']] = row

        for r in recordings:
            try:
                row = mbid_index[r.mbid]
            except KeyError:
                if debug:
                    print("- debug recording MBID %s not found, skipping." % r.mbid)
                continue

            if not r.artist:
                a = Artist(name=row['artist_credit_name'],
                           mbids=row.get('[artist_credit_mbids]', []),
                           artist_credit_id=row['artist_credit_id'])
                r.artist = a
            else:
                r.artist.name = row['artist_credit_name']
                r.artist.mbids = row.get('[artist_credit_mbids]', []),
                r.artist.artist_credit_id = row['artist_credit_id']

            r.name = row['recording_name']
            r.length = row['length']

        return recordings
