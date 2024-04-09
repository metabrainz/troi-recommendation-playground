import logging

from troi import Element, Artist, ArtistCredit, Release, Recording
import liblistenbrainz
import liblistenbrainz.errors

logger = logging.getLogger(__name__)


class UserArtistsElement(Element):
    '''
        Fetch artist statistics from ListenBrainz.

        :param user_name: The ListenBrainz user for whom to fetch statistics.
        :param time_range: The time range for which to fetch stats.
        :param count: The number of items to return. Default 25.
        :param offset: The offset into the results. Used for pagination.
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time', auth_token=None):
        super().__init__()
        self.client = liblistenbrainz.ListenBrainz()
        if auth_token:
            self.client.set_auth_token(auth_token)
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [ArtistCredit]

    def read(self, inputs=[]):

        artist_list = []
        artists = self.client.get_user_artists(self.user_name, self.count, self.offset, self.time_range)
        artist_credits = []
        for a in artists['payload']['artists']:
            artists = [Artist(mbid=mbid) for mbid in a['artist_mbids']]
            artist_list.append(ArtistCredit(name=a['artist_name'], artists=artists))

        return artist_list


class UserReleasesElement(Element):
    '''
        Fetch release statistics from ListenBrainz

        :param user_name: The ListenBrainz user for whom to fetch statistics.
        :param time_range: The time range for which to fetch stats.
        :param count: The number of items to return. Default 25.
        :param offset: The offset into the results. Used for pagination.
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time', auth_token=None):
        super().__init__()
        self.client = liblistenbrainz.ListenBrainz()
        if auth_token:
            self.client.set_auth_token(auth_token)
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Release]

    def read(self, inputs=[]):

        release_list = []
        releases = self.client.get_user_releases(self.user_name, self.count, self.offset, self.time_range)
        for r in releases['payload']['releases']:
            artists = [Artist(mbid=mbid) for mbid in r['artist_mbids']]
            release_list.append(
                Release(r['release_name'],
                        mbid=r['release_mbid'],
                        artist_credit=ArtistCredit(name=r['artist_name'], artists=artists)))

        return release_list


class UserRecordingElement(Element):
    '''
        Fetch release statistics from ListenBrainz

        :param user_name: The ListenBrainz user for whom to fetch statistics.
        :param time_range: The time range for which to fetch stats.
        :param count: The number of items to return. Default 25.
        :param offset: The offset into the results. Used for pagination.
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time'):
        super().__init__()
        self.client = liblistenbrainz.ListenBrainz()
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Recording]

    def read(self, inputs=[]):
        recording_list = []
        try:
            recordings = self.client.get_user_recordings(self.user_name, self.count, self.offset, self.time_range)
        except liblistenbrainz.errors.ListenBrainzAPIException as err:
            logger.info("Cannot fetch recording stats for user %s" % self.user_name)
            return []

        if recordings is None or "recordings" not in recordings['payload']:
            return []

        for r in recordings['payload']['recordings']:
            artists = [Artist(mbid=mbid) for mbid in r['artist_mbids']]
            artist_credit = ArtistCredit(r['artist_name'], artists=artists)
            release = Release(r['release_name'], mbid=r['release_mbid'])
            recording_list.append(Recording(r['track_name'], mbid=r['recording_mbid'], artist_credit=artist_credit,
                                            release=release))

        return recording_list
