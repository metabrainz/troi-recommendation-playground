import click

import troi.filters
import troi.listenbrainz.stats
import troi.musicbrainz.mbid_mapping
import troi.musicbrainz.recording
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.genre_lookup
import troi.sorts
from troi import Recording
from troi.listenbrainz.similar_recordings import LookupSimilarRecordingsElement
from troi.filters import FirstArtistCreditFilterElement


@click.group()
def cli():
    pass


class SimilarRecordingsPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Recordings similar to recording %s from %s"
    DESC = """<p>
                Given a seed track, return a playlist of tracks that are similar.
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('recording_mbid')
    @click.argument('algorithm')
    def parse_args(**kwargs):
        """
        Generate a year in review playlist.

        \b
        RECORDING_MBID: Seed track for similarity search.
        ALGORITHM: index algorithm to use.
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "recording_mbid", "desc": "Seed recording", "optional": False },
                { "type": str, "name": "algorithm", "desc": "Which index algorithm to use", "optional": False }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "similar-recordings"

    @staticmethod
    def description():
        return "Generate a playlist from the similar tracks for a given tack."

    def create(self, inputs):
        mbid = inputs['recording_mbid']
        alg = inputs['algorithm']

        recording = troi.musicbrainz.recording.RecordingListElement([Recording(mbid=mbid)])

        similar = LookupSimilarRecordingsElement(algorithm=alg, count=100)
        similar.set_sources(recording)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(similar)

        ac_filter = FirstArtistCreditFilterElement()
        ac_filter.set_sources(recs_lookup) 

        genre_lookup = troi.musicbrainz.genre_lookup.GenreLookupElement(count_threshold=0)
        genre_lookup.set_sources(ac_filter)

        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (mbid, alg),
                                                      self.DESC,
                                                      max_num_recordings=100)
        pl_maker.set_sources(genre_lookup)

        return pl_maker
