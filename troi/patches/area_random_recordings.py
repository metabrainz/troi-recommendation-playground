import datetime

from troi import PipelineError, Recording
import troi.listenbrainz.area_random_recordings
import troi.tools.area_lookup
import troi.musicbrainz.recording_lookup
import troi.patch
import troi.filters


class AreaRandomRecordingsPatch(troi.patch.Patch):

    def __init__(self, debug=False):
        super().__init__(debug)

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "area", "desc": "MusicBrainz area from which to choose tracks.", "optional": False },
                { "type": int, "name": "start_year", "desc": "Start year", "optional": False },
                { "type": int, "name": "end_year", "desc": "End year", "optional": False }]

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
        area_name = inputs[0]
        start_year = inputs[1]
        end_year = inputs[2]

        area_id = troi.tools.area_lookup.area_lookup(area_name)

        if not start_year or start_year < 1800 or start_year > datetime.datetime.today().year:
            raise PipelineError("start_year must be given and be an integer between 1800 and the current year.")

        if not end_year or end_year < 1800 or end_year > datetime.datetime.today().year:
            raise PipelineError("end_year must be given and be an integer between 1800 and the current year.")

        if end_year < start_year:
            raise PipelineError("end_year must be equal to or greater than start_year.")

        area = troi.listenbrainz.area_random_recordings.AreaRandomRecordingsElement(area_id, start_year, end_year)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(area)

        artist_limiter = troi.filters.ArtistCreditLimiterElement()
        artist_limiter.set_sources(r_lookup)

        return artist_limiter
