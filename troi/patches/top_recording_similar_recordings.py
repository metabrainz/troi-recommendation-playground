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
import troi.musicbrainz.mbid_mapping


@click.group()
def cli():
    pass

class LookupSimilarRecordingsElement(Element):
    """ Lookup similar recordings.

        Given a list of recordings, this element will output recordings that are similar to the ones passed in.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        sim = []
        for recording in inputs[0]:
            url = f"https://labs.api.listenbrainz.org/similar-recordings/json"
            r = requests.get(url, { "recording_mbid": recording.mbid, "algorithm": "session_based_days_7_session_300" })
            if r.status_code != 200:
                logger.info("Fetching similar recordings failed: %d. Skipping." % r.status_code)
                continue

            data = r.json()
            try:
                sim.append(Recording(mbid=data[3]["data"][0]["recording_mbid"]))
                sim.append(Recording(mbid=data[3]["data"][1]["recording_mbid"]))
            except IndexError:
                pass

        return sim
             


class TopRecordingsSimilarRecordingsPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Recordings Similar to your top Recordings"
    DESC = """<p>
               Given your top recordings for the last %s, 
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    @click.argument('time_range')
    def parse_args(**kwargs):
        """
        Generate a year in review playlist.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        TIME_RANGE: staticstics range: week, month, year, all. 
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "user_name", "desc": "ListenBrainz user name", "optional": False },
                { "type": str, "name": "range", "desc": "Statistics time range (week, month, year, ...)", "optional": False }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "recordings-similar-to-top-recordings"

    @staticmethod
    def description():
        return "Generate a playlist of tracks that are similar to your top tracks."

    def create(self, inputs):
        user_name = inputs['user_name']
        time_range = inputs['time_range']

        stats = troi.listenbrainz.stats.UserRecordingElement(user_name=user_name,
                                                             count=100,
                                                             time_range=time_range)

        remove_empty = troi.filters.EmptyRecordingFilterElement()
        remove_empty.set_sources(stats)

        similar = LookupSimilarRecordingsElement()
        similar.set_sources(remove_empty)

        dedup = troi.filters.DuplicateRecordingMBIDFilterElement()
        dedup.set_sources(similar)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(dedup)

        ac_limiter = troi.filters.ArtistCreditLimiterElement(count=2)
        ac_limiter.set_sources(recs_lookup)

        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME,
                                                      self.DESC,
                                                      max_num_recordings=50)
        pl_maker.set_sources(ac_limiter)

        return pl_maker
