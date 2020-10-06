import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup


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

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user, artist_type=type, count=200)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(recs)

        return r_lookup
