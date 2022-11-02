import click

import troi.filters
import troi.listenbrainz.spotify_id_lookup
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

    NAME = "Recordings similar to '%s' by '%s'"
    DESC = """<p>
                This test playlist contains recordings that are similar to the seed track
                '%s' by '%s'. Similarity algorithm used: %s
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings
        self.algorithm = None

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('recording_mbid')
    @click.argument('algorithm')
    def parse_args(**kwargs):
        """
        Generate a playlist from similar track data, keeping the seed track and removing
        more tracks by the seed artist.

        \b
        RECORDING_MBID: Seed track for similarity search.
        ALGORITHM: index algorithm to use.
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{
            "type": str,
            "name": "recording_mbid",
            "desc": "Seed recording",
            "optional": False
        }, {
            "type": str,
            "name": "algorithm",
            "desc": "Which index algorithm to use",
            "optional": False
        }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "similar-recordings"

    @staticmethod
    def description():
        return "Generate a playlist from the similar tracks for a given tack."

    def set_playlist_metadata(self, playlist):
        try:
            seed_recording = playlist.recordings[0]
        except (IndexError, KeyError):
            return
        playlist.name = self.NAME % (seed_recording.name, seed_recording.artist.name)
        playlist.description = self.DESC % (seed_recording.name, seed_recording.artist.name, self.algorithm)

    def create(self, inputs):
        mbid = inputs['recording_mbid']
        self.algorithm = inputs['algorithm']

        recording = troi.musicbrainz.recording.RecordingListElement([Recording(mbid=mbid)])

        similar = LookupSimilarRecordingsElement(algorithm=self.algorithm, count=100, keep_seed=True)
        similar.set_sources(recording)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(similar)

        ac_filter = FirstArtistCreditFilterElement()
        ac_filter.set_sources(recs_lookup)

        spotify_lookup = troi.listenbrainz.spotify_id_lookup.SpotifyIdLookupElement()
        spotify_lookup.set_sources(ac_filter)

        pl_maker = troi.playlist.PlaylistMakerElement(max_num_recordings=100, source_patch=self)
        pl_maker.set_sources(spotify_lookup)

        return pl_maker
