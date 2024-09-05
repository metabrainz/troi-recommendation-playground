import logging
from time import sleep

import requests

import troi.patch
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.plist import plist
from troi import Element, ArtistCredit, Recording, PipelineError, DEVELOPMENT_SERVER_URL

logger = logging.getLogger(__name__)


class LBRadioCountryRecordingElement(Element):
    '''
        Given a country, return recordings for that country.

        Arguments:
            area_name: the name of the area to make a playlist for
    '''

    def __init__(self, mode, area_name=None, area_mbid=None):
        super().__init__()
        self.area_name = area_name
        self.area_mbid = str(area_mbid)
        self.mode = mode

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def lookup_area_by_name(self, area_name):

        while True:
            r = requests.get("https://musicbrainz.org/ws/2/area?query=%s&fmt=json" % area_name)
            if r.status_code in (503, 429):
                sleep(1)
                continue

            if r.status_code != 200:
                raise PipelineError("Cannot fetch country code from MusicBrainz. HTTP code %s" % r.status_code)

            try:
                area = r.json()['areas'][0]
            except IndexError:
                return None

            if area["type"] == "Country":
                return area["id"]
            else:
                return None

    def lookup_area_by_mbid(self, area_mbid):

        while True:
            r = requests.get("https://musicbrainz.org/ws/2/area/%s?fmt=json" % area_mbid)
            if r.status_code in (503, 429):
                sleep(1)
                continue

            if r.status_code != 200:
                raise PipelineError("Cannot fetch country code from MusicBrainz. Error: %s" % r.text)

            area = r.json()
            if area["type"] != "Country":
                raise PipelineError("The specified area_mbid (%s) refers to a %s, but only countries are supported." %
                                    (area_mbid, area["type"]))

            return area["name"]

    def recording_from_row(self, row):
        if row['recording_mbid'] is None:
            return None

        r = Recording(mbid=row['recording_mbid'])
        if 'artist_credit_name' in row:
            r.artist = ArtistCredit(name=row['artist_credit_name'])

        if 'recording_name' in row:
            r.name = row['recording_name']

        if 'year' in row:
            r.year = row['year']

        if 'listen_count' in row:
            r.listenbrainz = {"listen_count": row["listen_count"]}

        return r

    def read(self, inputs):

        start, stop = {"easy": (66, 100), "medium": (33, 66), "hard": (0, 33)}[self.mode]

        if self.area_name is None and self.area_mbid is None:
            raise PipelineError("An area name or area mbid must be specified.")

        if self.area_name:
            self.area_mbid = self.lookup_area_by_name(self.area_name)
            if self.area_mbid is None:
                raise PipelineError("Cannot find country '%s'" % self.area_name)
        else:
            self.area_name = self.lookup_area_by_mbid(self.area_mbid)
            if self.area_name is None:
                raise PipelineError("Cannot lookup country from mbid '%s'" % self.area_mbid)

        args = [{"[area_mbid]": self.area_mbid}]
        r = requests.post(DEVELOPMENT_SERVER_URL + "/popular-recordings-by-country/json", json=args)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch first dataset recordings from ListenBrainz. HTTP code %s (%s)" %
                                (r.status_code, r.text))

        self.data_cache = self.local_storage["data_cache"]
        self.data_cache["element-descriptions"].append("country %s" % self.area_name)

        recordings = plist()
        for row in r.json():
            recordings.append(self.recording_from_row(row))

        return recordings.random_item(start, stop, TARGET_NUMBER_OF_RECORDINGS)
