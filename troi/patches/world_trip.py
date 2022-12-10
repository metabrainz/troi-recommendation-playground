from collections import defaultdict
from urllib.parse import quote

import countryinfo
import requests

import troi.patch
from troi import Element, Artist, Recording, Playlist, PipelineError, DEVELOPMENT_SERVER_URL


def recording_from_row(row):
    if row['recording_mbid'] is None:
        return None

    r = Recording(mbid=row['recording_mbid']) 
    if 'artist_credit_name' in row:
        r.artist = Artist(name=row['artist_credit_name'])

    if 'recording_name' in row:
        r.name = row['recording_name']

    if 'year' in row:
        r.year = row['year']

    if 'listen_count' in row:
        r.listenbrainz={"listen_count": row["listen_count"]}

    return r


class WorldTripElement(Element):
    '''
        Given a continent (africa, americas, asia, europe, oceania) and
        a sort order latitude or longitude, pick random tracks from each country and
        add tracks to a playlist sorted by latitude or longitude.

        Arguments:
            continent: one of: (Africa, North America, South America, Asia, Europe, Oceania)
            latitude: boolean. Sort by latiduded if True, otherwise sort by longitude
    '''

    def __init__(self, continent, latitude):
        super().__init__()
        self.continent = continent
        self.latitude = latitude

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        countries = countryinfo.CountryInfo().all()

        continents = defaultdict(list)
        for country in countries.values():
            if 'region' not in country:
                continue

            continents[country['region'].lower()].append({'name': country['name'],
                                                  'code': country['ISO']['alpha2'], 
                                                  'latlng': country['latlng'] })

        if self.continent not in continents:
            names = continents.keys()
            raise RuntimeError(f"Cannot find continent {self.continent}. Must be one of {names}")

        print("Fetch tracks from countries:")
        if self.latitude:
            continent = sorted(continents[self.continent], key=lambda c: c['latlng'][0], reverse=True)
        else:
            continent = sorted(continents[self.continent], key=lambda c: c['latlng'][1])

        for i, country in enumerate(continent):
            self.debug("   %s" % country["name"])

            r = requests.get("http://musicbrainz.org/ws/2/area?query=%s&fmt=json" % country['name'])
            if r.status_code != 200:
                raise PipelineError("Cannot fetch country code from MusicBrainz. HTTP code %s" % r.status_code)

            country_code = r.json()['areas'][0]['id']
            r = requests.post(DEVELOPMENT_SERVER_URL + "/area-random-recordings/json", json=[{ "area_mbid": country_code,
                                "start_year": 2012,
                                "end_year": 2021 }])
            if r.status_code != 200:
                raise PipelineError("Cannot fetch first dataset recordings from ListenBrainz. HTTP code %s (%s)" % (r.status_code, r.text))

            recordings = []
            for row in r.json():
                recordings.append(recording_from_row(row))

            country["recordings"] = recordings


        recordings = []
        for i in range(3):
            for country in continent:
                try:
                    recordings.append(country["recordings"][i])
                except KeyError:
                    print("Found no tracks for %s" % country["name"])
                except IndexError:
                    print("Found too few tracks for %s" % country["name"])

        return recordings


class WorldTripPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Three trips across %s with ListenBrainz (%s)"
    DESC = """<p>
                This playlist contains randomly selected tracks from the last few years released in 
                the countries of %s, arranged from %s. Once the playlist reaches the southernmost
                country, the list repeats twice more, for a total of three trips across the continent.
              </p>
           """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    def inputs():
        """
        Generate a playlist that picks tracks for each country in a continent.

        \b
        CONTINENT: A name of a continent, all lower case.
        SORT: Must be longitude or latitude
        """
        return [
            {"type": "argument", "args": ["continent"]},
            {"type": "argument", "args": ["sort"]}
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "world-trip"

    @staticmethod
    def description():
        return "Generate a playlist for a given continent"

    def create(self, inputs):

        if inputs["sort"] not in ("longitude", "latitude"):
            raise PipelineError("Argument sort must be either 'longitude' or 'latitude'.")

        if inputs["sort"] == "longitude":
            latitude = False
            lat_string = "North -> South"
        elif inputs["sort"] == "latitude":
            latitude = True
            lat_string = "West -> East"
        else:
            raise RuntimeError("sort must be longitude or latitude")

        trip = WorldTripElement(inputs['continent'], latitude)
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (inputs["continent"], lat_string),
                                                      self.DESC % (quote(inputs["continent"]), lat_string))
        pl_maker.set_sources(trip)

        return pl_maker
