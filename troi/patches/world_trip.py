import logging
from time import sleep
from collections import defaultdict
from urllib.parse import quote

import countryinfo
import requests

import troi.patch
from troi.splitter import plist
from troi import Element, Artist, ArtistCredit, Recording, Playlist, PipelineError, DEVELOPMENT_SERVER_URL

logger = logging.getLogger(__name__)


class AreaPlaylistElement(Element):
    '''
        Given an area / country, generate a playlist for that country.

        Arguments:
            area_name: the name of the area to make a playlist for
    '''

    def __init__(self, area_name):
        super().__init__()
        self.area_name = area_name

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def lookup_area(self, area_name):

        while True:
            r = requests.get("http://musicbrainz.org/ws/2/area?query=%s&fmt=json" % area_name)
            if r.status_code == 503:
                sleep(1)
                continue

            if r.status_code != 200:
                raise PipelineError("Cannot fetch country code from MusicBrainz. HTTP code %s" % r.status_code)

            return r.json()['areas'][0]['id']

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
            r.listenbrainz={"listen_count": row["listen_count"]}

        return r


    def read(self, inputs):

        area_mbid = self.lookup_area(self.area_name)
        args = [ { "[area_mbid]": area_mbid } ]
        r = requests.post(DEVELOPMENT_SERVER_URL + "/popular-recordings-by-country/json", json=args)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch first dataset recordings from ListenBrainz. HTTP code %s (%s)" % (r.status_code, r.text))

        recordings = []
        for row in r.json():
            recordings.append(self.recording_from_row(row))

        return recordings


class AreaPlaylistPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Welcome to %s!"
    DESC = "This playlist contains randomly selected top tracks released by artists who are from %s"

    def __init__(self, args):
        self.area_name = args["area_name"]
        troi.patch.Patch.__init__(self, args)

    @staticmethod
    def inputs():
        """
        Generate a playlist that picks tracks for an area / country.

        \b
        AREA_NAME: A name of a country.
        """
        return [
            {"type": "argument", "args": ["area_name"]}
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "area-playlist"

    @staticmethod
    def description():
        return "Generate a playlist for a given area (country)."

    def create(self, inputs):

        area_name = self.area_name
        area_name = self.area_name[0:1].upper() + self.area_name[1:]

        trip = AreaPlaylistElement(area_name)
        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(trip)
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (area_name),
                                                      self.DESC % (quote(area_name)),
                                                      shuffle=True)
        pl_maker.set_sources(recs_lookup)

        return pl_maker
