import troi.filters
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi.acousticbrainz.annoy import AnnoyLookupElement


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

        if similarity_type not in ("mfccs", "bpm"):
            raise RuntimeError("type must be either 'mfccs' or 'bpm'")

        annoy = AnnoyLookupElement(similarity_type, recording_id)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(annoy)
        remove_dups = troi.filters.DuplicateRecordingFilterElement()
        remove_dups.set_sources(r_lookup)

        return remove_dups
