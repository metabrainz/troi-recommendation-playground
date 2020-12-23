from collections import defaultdict
from urllib.parse import quote
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

    NAME = "Top discoveries of 2020 for %s"
    DESC = """<p>
              We generated this playlist from your <a href="https://listenbrainz.org/user/%s/reports?range=year">
              listening statistics for 2020</a>. We started with all the recordings that you first listened to in
              2020 and then selected the recordings that you listened to more than once. If we found recordings 
              from more than 15 artists, we selected at most 2 recordings from each artist to make this playlist.
              If we found 15 or fewer artists, we picked all the recordings. Finally, we returned at most 30 
              recordings and ordered them by how many times you listened to them in 2020.
              </p>
              <p>
              Double click on any recording to start playing it -- we'll do our best to find a matching recording
              to play. If you have Spotify, we recommend connecting your account for a better playback experience.
              </p>
              <p>
              Please keep in mind that this is our first attempt at making playlists for our users. Our processes
              are not fully debugged and you may find that things are not perfect. So, if this playlist isn't
              very accurate, we apologize -- we'll continue to make them better. (e.g. some recordings may be missing
              from this list because we were not able to find a match for it in MusicBrainz.)
              </p>
              <p>
              Happy holidays from everyone at MetaBrainz!
              </p>
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

        pl_maker = troi.patches.top_tracks_for_year.PlaylistMakerElement(self.NAME % user_name, self.DESC % quote(user_name))
        pl_maker.set_sources(shaper)

        return pl_maker
