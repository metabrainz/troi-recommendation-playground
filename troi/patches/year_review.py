from collections import defaultdict
import requests

import click

from troi import Element, Artist, Recording, Playlist, PipelineError
import troi.listenbrainz.recs
import troi.filters
import troi.sorts
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.year_lookup
import troi.patches.top_tracks_for_year


@click.group()
def cli():
    pass

class YearReviewFetcherElement(Element):
    '''
    '''
    SERVER_URL = "https://datasets.listenbrainz.org/first-listened-to-2020/json"

    def __init__(self, user_name, minimum_count=20):
        super().__init__()
        self.user_name = user_name
        self.minimum_count = minimum_count

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):

        data = [{ 'user_name': self.user_name }]
        r = requests.post(self.SERVER_URL, json=data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch first listened recordings from ListenBrainz. HTTP code %s" % r.status_code)

        recordings = []
        for row in r.json():
            recordings.append(Recording(mbid=row['recording_mbid'], 
                                        name=row['recording_name'], 
                                        listenbrainz={"listen_count": row["listen_count"]},
                                        artist=Artist(name=row['artist_credit_name'],
                                                      artist_credit_id=row['artist_credit_id'])))

            self.debug("%-60s %-50s %d" % (row['recording_name'][:59], row['artist_credit_name'][:49], row["listen_count"]))

        return recordings


class YearReviewShaperElement(Element):
    '''
    '''

    def __init__(self, artist_count=15, max_num_recordings=30):
        super().__init__()
        self.artist_count = artist_count
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):

        recordings = inputs[0]

        artists = defaultdict(int)
        for r in recordings:
            artists[r.artist.artist_credit_id] += 1

        if len(artists.keys()) > self.artist_count:
            self.debug("returned filtered year review list")
            filtered = []
            artists = defaultdict(int)
            for r in recordings:
                if artists[r.artist.artist_credit_id] < 2: 
                    filtered.append(r)
                    artists[r.artist.artist_credit_id] += 1

            return filtered[:self.max_num_recordings]
        else:
            self.debug("returned full year review list")

        return recordings[:self.max_num_recordings]


class YearReview(troi.patch.Patch):
    """
        See below for description
    """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('user_name')
    def parse_args(**kwargs):
        """
        Generate a year in review playlist.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        """

        return kwargs

    @staticmethod
    def inputs():
        return [{ "type": str, "name": "user_name", "desc": "ListenBrainz user name", "optional": False }]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "year-review"

    @staticmethod
    def description():
        return "Generate your year in review playlist."

    def create(self, inputs):
        user_name = inputs['user_name']

        recs = YearReviewFetcherElement(user_name=user_name)

        shaper = YearReviewShaperElement()
        shaper.set_sources(recs)

        pl_maker = troi.patches.top_tracks_for_year.PlaylistMakerElement("Top discoveries of 2020",
                                                                         "Top tracks you started listening to in 2020.")
        pl_maker.set_sources(shaper)

        return pl_maker
