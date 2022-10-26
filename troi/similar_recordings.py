from datetime import datetime 
from collections import defaultdict
from urllib.parse import quote
import requests

import click

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.listenbrainz.stats
import troi.filters
import troi.sorts
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.recording
import troi.musicbrainz.mbid_mapping


@click.group()
def cli():
    pass

class LookupSimilarRecordingsElement(Element):
    """ Lookup similar recordings.

        Given a list of recordings, this element will output recordings that are similar to the ones passed in.
    """

    def __init__(self, recording_mbid, alg):
        super().__init__()
        self.recording_mbid = recording_mbid
        self.alg = alg

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        sim = [inputs[0][0]]
        for recording in inputs[0]:
            url = f"https://labs.api.listenbrainz.org/similar-recordings/json"
            r = requests.get(url, { "recording_mbid": self.recording_mbid, "algorithm": self.alg })
            if r.status_code != 200:
                logger.info("Fetching similar recordings failed: %d. Skipping." % r.status_code)
                continue

            data = r.json()
            try:
                for recording in data[3]["data"]:
                    sim.append(Recording(mbid=recording["recording_mbid"]))
            except IndexError:
                pass

        return sim
             

class FirstArtistCreditFilterElement(troi.Element):
    '''
        Remove all recordings by the artist credit of the FIRST recording in the stream.
    '''

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recording = inputs[0][0]
        acs = recording.artist.mbids

        results = []
        for i, r in enumerate(inputs[0]):
            if i == 0:
                results.append(r)
                continue

            skip = False
            for rec_artist in r.artist.mbids:
                if rec_artist in acs:
                    skip = True
                    break

            if skip:
                continue

            results.append(r)

        return results

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

        similar = LookupSimilarRecordingsElement(mbid, alg)
        similar.set_sources(recording)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(similar)

        ac_filter = FirstArtistCreditFilterElement()
        ac_filter.set_sources(recs_lookup) 

        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (mbid, alg),
                                                      self.DESC,
                                                      max_num_recordings=50)
        pl_maker.set_sources(ac_filter)

        return pl_maker
