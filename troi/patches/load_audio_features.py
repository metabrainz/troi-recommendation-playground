import click

import troi.filters
import troi.listenbrainz.spotify_id_lookup
import troi.listenbrainz.spotify_audio_features
import troi.musicbrainz.mbid_mapping
import troi.musicbrainz.recording
import troi.musicbrainz.recording_lookup
import troi.sorts
from troi import Recording
from troi.listenbrainz.similar_recordings import LookupSimilarRecordingsElement
from troi.filters import FirstArtistCreditFilterElement


@click.group()
def cli():
    pass


class LoadAudioFeaturesPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Make a playlist from given MBIDs and load their Spotify audio features"
    DESC = """<p>
                This test playlist contains recordings that are similar to the seed track
                '%s' by '%s'. Similarity algorithm used: %s
              </p>
           """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('recording_mbid0')
    @click.argument('recording_mbid1')
    def parse_args(**kwargs):
        """
        Compare two recordings using spotify audio features.

        \b
        RECORDING_MBID0: fist recording
        RECORDING_MBID1: second recording
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{
            "type": str,
            "name": "recording_mbid0",
            "desc": "recording 0",
            "optional": False
        }, {
            "type": str,
            "name": "recording_mbid1",
            "desc": "recording 1",
            "optional": False
        }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "load-audio-features"

    @staticmethod
    def description():
        return "Generate a playlist for two recordings and load their spotify audio features"

    def create(self, inputs):
        mbid0 = inputs['recording_mbid0']
        mbid1 = inputs['recording_mbid1']

        recording = troi.musicbrainz.recording.RecordingListElement([Recording(mbid=mbid0), Recording(mbid=mbid1)])

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(recording)

        spotify_lookup = troi.listenbrainz.spotify_id_lookup.SpotifyIdLookupElement()
        spotify_lookup.set_sources(recs_lookup)

        spotify_features = troi.listenbrainz.spotify_audio_features.SpotifyAudioFeaturesElement()
        spotify_features.set_sources(spotify_lookup)

        pl_maker = troi.playlist.PlaylistMakerElement(max_num_recordings=100, source_patch=self)
        pl_maker.set_sources(spotify_features)

        return pl_maker
