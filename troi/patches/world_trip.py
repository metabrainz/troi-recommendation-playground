from collections import defaultdict 
from operator import attrgetter
from urllib.parse import quote

import click
import requests
import countryinfo

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.patch


@click.group()
def cli():
    pass

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
        Given a continent (Africa, North America, South America, Asia, Europe, Oceania) and
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
        return [Playlist]

    def read(self, inputs):

        countries = countryinfo.CountryInfo().all()

        continents = defaultdict(list)
        for country in countries.values():
            if 'region' not in country:
                continue

            continents[country['region']].append({'name': country['name'],
                                                  'code': country['ISO']['alpha2'], 
                                                  'latlng': country['latlng'] })

        print("Fetch tracks from countries:")
        if self.latitude:
            continent = sorted(continents[self.continent], key=lambda c: c['latlng'][0], reverse=True)
        else:
            continent = sorted(continents[self.continent], key=lambda c: c['latlng'][1])

        for i, country in enumerate(continent):
            self.debug("   ", country["name"])

            r = requests.get("http://musicbrainz.org/ws/2/area?query=%s&fmt=json" % country['name'])
            if r.status_code != 200:
                raise PipelineError("Cannot fetch country code from MusicBrainz. HTTP code %s" % r.status_code)

            country_code = r.json()['areas'][0]['id']
            r = requests.post("https://bono.metabrainz.org/area-random-recordings/json", json=[{ "area_mbid": country_code,
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
    @cli.command(no_args_is_help=True)
    @click.argument('continent')
    @click.argument('sort')
    def parse_args(**kwargs):
        """

        """

        return kwargs

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "continent", "desc": "continent to generate playlist for", "optional": False },
                { "type": str, "name": "sort", "desc": "Sort by latitude (north->south), longitude (west->east)", "optional": False }]

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
        else:
            latitude = True
            lat_string = "West -> East"

        trip = WorldTripElement(inputs['continent'], latitude)
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (inputs["continent"], lat_string),
                                                      self.DESC % (quote(inputs["continent"]), lat_string))
        pl_maker.set_sources(trip)

        return pl_maker
