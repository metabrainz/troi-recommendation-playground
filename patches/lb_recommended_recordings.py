from troi import Element
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup


class DailyJamsElement(Element):
    '''
        Split weekly recommended recordings into 7 sets, one for each day of the week.
    '''

    def __init__(self, recs):
        Element.__init__(self)
        self.recs = recs

    def outputs(self):
        return [Recording]

    def read(self, inputs = []):
        print(self.recs.last_updated)

        return inputs[0]


class LBRecommendedRecordingsPatch(troi.patch.Patch):

    def inputs(self):
        return [(str, "user"), (str, "type")]

    def slug(self):
        return "lb-recommended-recordings"

    def description(self):
        return "Generate a playlist from the ListenBrainz recommended recordings"

    def create(self, inputs):
        user_name = inputs[0]
        type = inputs[1]

        if type not in ("top", "similar"):
            raise RuntimeError("type must be either 'top' or 'similar'")

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name, artist_type=type, count=200)
        jams = DailyJamsElement(recs)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()

        jams.set_sources(recs)
        r_lookup.set_sources(jams)

        return r_lookup
