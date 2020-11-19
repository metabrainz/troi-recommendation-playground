import click

import troi
import troi.patch
import troi.filters
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi.acousticbrainz import annoy


@click.group()
def cli():
    pass


class ABSimilarRecordingsPatch(troi.patch.Patch):

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('recording_id')
    @click.argument('similarity_type')
    def parse_args(**kwargs):
        """
        Find acoustically similar recordings from AcousticBrainz.

        \b
        RECORDING_ID: A musicbrainz recording ID to find similar recordings to
        SIMILARITY_TYPE: an annoy similarity type to use when finding similar recordings
        """
        return kwargs

    @staticmethod
    def slug():
        return "ab-similar-recordings"

    @staticmethod
    def description():
        return "Find acoustically similar recordings from AcousticBrainz"

    def create(self, inputs):
        recording_id = inputs[0]
        similarity_type = inputs[1]

        annoy_element = annoy.AnnoyLookupElement(similarity_type, recording_id)
        r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        r_lookup.set_sources(annoy_element)
        remove_none = troi.filters.EmptyRecordingFilterElement()
        remove_none.set_sources(r_lookup)
        remove_dups = troi.filters.DuplicateRecordingFilterElement()
        remove_dups.set_sources(remove_none)

        return remove_dups
