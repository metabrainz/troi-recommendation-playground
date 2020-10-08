import sys
import uuid
from urllib.parse import quote

import requests
import ujson

from troi import Element, Artist, Recording

def area_lookup(area_name):
    '''
        Given an area name, lookup the area_id and return it. Return None if area not found.
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/area-lookup/json"
    data = [ { '[area]': area_name } ]
    r = requests.post(SERVER_URL, json=data)
    if r.status_code != 200:
        raise RuntimeError("Cannot lookup area name. " + str(r.text))

    try:
        rows = ujson.loads(r.text)
    except Exception as err:
        raise RuntimeError(str(err))

    if len(rows) == 0:
        return None

    return rows[0]['area_id']
