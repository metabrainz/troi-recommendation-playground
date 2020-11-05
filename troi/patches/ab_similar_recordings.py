import troi.patch
import troi.filters
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import PipelineError
from troi.acousticbrainz.annoy import AnnoyLookupElement


VALID_METRICS = ['mfccs', 'mfccsw', 'gfccs', 'gfccsw', 'key', 'bpm', 'onsetrate', 'moods',
                 'instruments', 'dortmund', 'rosamerica', 'tzanetakis']


class ABSimilarRecordingsPatch(troi.patch.Patch):

    @staticmethod
    def inputs():
        return [
            {"type": str, "name": "recording_id", "desc": "MusicBrainz recording id", "optional": False},
            {"type": str, "name": "similarity_type", "desc": "Type of acousticbrainz similarity", "optional": False}]

    @staticmethod
    def slug():
        return "ab-similar-recordings"

    @staticmethod
    def description():
        return "Find acoustically similar recordings from AcousticBrainz"

    def create(self, inputs):
        recording_id = inputs[0]
        similarity_type = inputs[1]

        try:
            annoy = AnnoyLookupElement(similarity_type, recording_id)
        except PipelineError:
            raise RuntimeError(f"similarity_type must be one of {'.'.join(VALID_METRICS)}")

        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(annoy)
        remove_none = troi.filters.EmptyRecordingFilterElement()
        remove_none.set_sources(r_lookup)
        remove_dups = troi.filters.DuplicateRecordingFilterElement()
        remove_dups.set_sources(remove_none)

        return remove_dups
