import re
import sys
import uuid
from urllib.parse import quote

import requests
import ujson

from troi import Element, Artist, Recording, PipelineError

class YearLookupElement(Element):
    '''
        Look up musicbrainz earliest release year for a list of recordings, based on artist credit name and recording name.

        By default items that are not found in the year lookup are not returned by this element. Pass
        skip_not_found=False to init to keep tracks that failed the year lookup.

        :param skip_not_found: If this is True (the default) then any Recordings for which the year could not be lookd up will not be returned from this Element.
    '''

    SERVER_URL = "https://labs.api.listenbrainz.org/year-artist-recording-year-lookup/json"

    def __init__(self, skip_not_found=True):
        Element.__init__(self)
        self.skip_not_found = skip_not_found

    @staticmethod
    def inputs():
        return [ Recording ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs):

        recordings = inputs[0]
        if not recordings:
            return []

        data = []
        for r in recordings:
            try:
                data.append({ '[recording_name]': r.name, 
                              '[artist_credit_name]': r.artist.name })
            except AttributeError:
                raise PipelineError("YearLookupElement requires artist_credit_name and recording_name to exist.")

        r = requests.post(self.SERVER_URL, json=data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch recording years from MusicBrainz: HTTP code %d" % r.status_code)

        try:
            rows = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot fetch recording years from MusicBrainz: " + str(err))

        mbid_index = {}
        for row in rows:
            mbid_index[row['artist_credit_name'] + row['recording_name']] = row['year']

        output = []
        for r in recordings:
            try:
                r.year = mbid_index[r.artist.name + r.name]
            except KeyError:
                if self.skip_not_found:
                    self.debug("recording (%s %s) not found, skipping." % (r.artist.name, r.name))
                else:
                    output.append(r)
                continue

            output.append(r)

        return output
