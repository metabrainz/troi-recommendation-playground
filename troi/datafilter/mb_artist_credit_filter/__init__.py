import sys

import psycopg2
import psycopg2.extras

from troi.datafilter import DataFilter
from troi.lookup.mb_artist import MBArtistLookup
from troi import Entity, EntityEnum
from troi.operations import is_homogeneous


class MBArtistCreditFilter(DataFilter):
    '''
        Filter a recording list on if they belong (or not) to an artist. Recordings
        must have artist_mbids loaded.
    '''

    def __init__(self, db_connect_string):
        self.db_connect = db_connect_string


    def filter(self, recordings, artist_credits, exclude=True): 

        if not is_homogeneous(recordings, "recording"):
            raise TypeError("Recording list is not homogeneous.")

        if not is_homogeneous(artist_credits, "artist-credit"):
            raise TypeError("Artist credit list is not homogeneous.")

        ac_index = {}
        for ac in artist_credits:
            ac_index[ac.mb_artist['artist_credit_id']] = 1

        results = []
        for r in recordings:
            if r.mb_artist['artist_credit_id'] in ac_index:
                results.append(r)

        return results
