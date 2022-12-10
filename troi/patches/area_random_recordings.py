import datetime

from troi import PipelineError, Recording, DEVELOPMENT_SERVER_URL 
import troi.tools.area_lookup
import troi.musicbrainz.recording_lookup
import troi.patch
import troi.filters
from troi.playlist import PlaylistRedundancyReducerElement
from troi.listenbrainz.dataset_fetcher import DataSetFetcherElement


class AreaRandomRecordingsPatch(troi.patch.Patch):

    SERVER_URL = DEVELOPMENT_SERVER_URL + "/area-random-recordings/json"

    def __init__(self, debug=False):
        super().__init__(debug)

    @staticmethod
    def get_args():
        return [
            {
                "type": "argument",
                "args": ["area"],
                "kwargs": {}
            },
            {
                "type": "argument",
                "args": ["start_year"],
                "kwargs": {
                    "type": int,
                }
            },
            {
                "type": "argument",
                "args": ["end_year"],
                "kwargs": {
                    "type": int,
                }
            }
        ]

    @staticmethod
    def get_documentation():
        return """
        Generate a list of random recordings from a given area.

        \b
        AREA is a MusicBrainz area from which to choose tracks.
        START_YEAR is the start year.
        END_YEAR is the end year.
        """

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "area-random-recordings"

    @staticmethod
    def description():
        return "Generate a list of random recordings from a given area."

    def create(self, inputs):
        area_name = inputs['area']
        start_year = inputs['start_year']
        end_year = inputs['end_year']

        area_id = troi.tools.area_lookup.area_lookup(area_name)

        if not start_year or start_year < 1800 or start_year > datetime.datetime.today().year:
            raise PipelineError("start_year must be given and be an integer between 1800 and the current year.")

        if not end_year or end_year < 1800 or end_year > datetime.datetime.today().year:
            raise PipelineError("end_year must be given and be an integer between 1800 and the current year.")

        if end_year < start_year:
            raise PipelineError("end_year must be equal to or greater than start_year.")

        recs = DataSetFetcherElement(server_url=self.SERVER_URL,
                                     json_post_data=[{ 'start_year': start_year,
                                                       'end_year': end_year,
                                                       'area_mbid': area_id }])

        name = "Random recordings from %s between %d and %d." % (area_name, start_year, end_year)
        pl_maker = troi.playlist.PlaylistMakerElement(name=name, desc=name)
        pl_maker.set_sources(recs)

        reducer = PlaylistRedundancyReducerElement()
        reducer.set_sources(pl_maker)

        return reducer
