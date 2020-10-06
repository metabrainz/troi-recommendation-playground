import troi.listenbrainz.area_random_recordings
import troi.tools.area_lookup
import troi.musicbrainz.recording_lookup
import troi.patch


class AreaRandomRecordingsPatch(troi.patch.Patch):

    def inputs(self):
        return [(str, "area"), (int, "start year"), (int, "end year")]

    def slug(self):
        return "area-random-recordings"

    def description(self):
        return "Generate a list of random recordings from a given area."

    def create(self, inputs):
        area_name = inputs[0]
        start_year = inputs[1]
        end_year = inputs[2]

        try:
            area_id = troi.tools.area_lookup.area_lookup(area_name)
        except RuntimeError as err:
            print("Cannot lookup area: ", str(err))
            return

        area = troi.listenbrainz.area_random_recordings.AreaRandomTracksElement(area_id, start_year, end_year)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(area)

        return r_lookup
