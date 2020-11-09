import troi
import troi.patch
import troi.filters
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi.acousticbrainz import annoy


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
            annoy_element = annoy.AnnoyLookupElement(similarity_type, recording_id)
        except troi.PipelineError as e:
            raise RuntimeError(str(e))

        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(annoy_element)
        remove_none = troi.filters.EmptyRecordingFilterElement()
        remove_none.set_sources(r_lookup)
        remove_dups = troi.filters.DuplicateRecordingFilterElement()
        remove_dups.set_sources(remove_none)

        return remove_dups
