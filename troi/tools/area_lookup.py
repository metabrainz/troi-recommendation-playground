import requests
from time import sleep
import ujson

from troi import PipelineError, DEVELOPMENT_SERVER_URL

AREA_LOOKUP_SERVER_URL = DEVELOPMENT_SERVER_URL + "/area-lookup/json"
def area_lookup(area_name):
    '''
        Given an area name, lookup the area_id and return it. Return None if area not found.
    '''

    data = [ { '[area]': area_name } ]
    while True:
        r = requests.post(AREA_LOOKUP_SERVER_URL, json=data)
        if r.status_code == 429:
            sleep(2)
            continue
        if r.status_code != 200:
            raise PipelineError("Cannot lookup area name. " + str(r.text))

        break

    try:
        rows = ujson.loads(r.text)
    except ValueError as err:
        raise PipelineError("Cannot lookup area name, invalid JSON returned: " + str(err))

    if len(rows) == 0:
        raise PipelineError("Cannot find area name. Must be spelled exactly as in MusicBrainz.")

    return rows[0]['area_mbid']
