import random

from troi import Element
import troi.listenbrainz.recs
import troi.filters
import troi.musicbrainz.recording_lookup


class DailyJamsElement(Element):
    '''
        Split weekly recommended recordings into 7 sets, one for each day of the week.
    '''

    def __init__(self, recs, day):
        Element.__init__(self)
        self.recs = recs
        self.day = day

    def inputs(self):
        return [Recording]

    def outputs(self):
        return [Recording]

    def read(self, inputs = [], debug=False):
        recordings = inputs[0]
        random.seed(self.recs.last_updated)
        random.shuffle(recordings)
        num_per_day = len(recordings) // 7
        days = [recordings[i:i + num_per_day] for i in range(0, len(recordings), num_per_day)]

        return days[self.day]


class DailyJamsPatch(troi.patch.Patch):

    def inputs(self):
        return [(str, "user"), (str, "type"), (int, "day")]

    def slug(self):
        return "daily-jams"

    def description(self):
        return "Generate a daily playlist from the ListenBrainz recommended recordings"

    def create(self, inputs):
        user_name = inputs[0]
        type = inputs[1]
        day = inputs[2]

        if type not in ("top", "similar"):
            raise RuntimeError("type must be either 'top' or 'similar'")

        recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user_name,
                                                                          artist_type=type,
                                                                          count=-1)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(recs)

        # If an artist should never appear in a playlist, add the artist_credit_id here
        artist_filter = troi.filters.ArtistCreditFilterElement([])
        artist_filter.set_sources(r_lookup)

        jams = DailyJamsElement(recs, day=day)
        jams.set_sources(artist_filter)

        return jams
