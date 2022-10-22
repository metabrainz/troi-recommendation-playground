from troi import Element, Artist, Release, Recording
import pylistenbrainz
import pylistenbrainz.errors


class UserArtistsElement(Element):
    '''
        Fetch artist statistics from ListenBrainz
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time', auth_token=None):
        super().__init__()
        self.client = pylistenbrainz.ListenBrainz()
        if auth_token:
            self.client.set_auth_token(auth_token)
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Artist]

    def read(self, inputs = []):

        artist_list = []
        artists = self.client.get_user_artists(self.user_name, self.count, self.offset, self.time_range)
        for a in artists['payload']['artists']:
            artist_list.append(Artist(a['artist_name'], mbids=a['artist_mbids']))

        return artist_list


class UserReleasesElement(Element):
    '''
        Fetch release statistics from ListenBrainz
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time', auth_token=None):
        super().__init__()
        self.client = pylistenbrainz.ListenBrainz()
        if auth_token:
            self.client.set_auth_token(auth_token)
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Release]

    def read(self, inputs = []):

        release_list = []
        releases = self.client.get_user_releases(self.user_name, self.count, self.offset, self.time_range)
        for r in releases['payload']['releases']:
            artist = Artist(r['artist_name'], mbids=r['artist_mbids'])
            release_list.append(Release(r['release_name'], mbid=r['release_mbid'], artist=artist))

        return release_list


class UserRecordingElement(Element):
    '''
        Fetch recording statistics from ListenBrainz
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time'):
        super().__init__()
        self.client = pylistenbrainz.ListenBrainz()
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Recording]

    def read(self, inputs = []):
        recording_list = []
        try:
            recordings = self.client.get_user_recordings(self.user_name, self.count, self.offset, self.time_range)
        except pylistenbrainz.errors.ListenBrainzAPIException as err:
            print("Cannot fetch recording stats for user %s" % self.user_name)
            return []

        if recordings is None or "recordings" not in recordings['payload']:
            return []

        for r in recordings['payload']['recordings']:
            artist = Artist(r['artist_name'], mbids=r['artist_mbids'])
            release = Release(r['release_name'], mbid=r['release_mbid'])
            recording_list.append(Recording(r['track_name'], mbid=r['recording_mbid'],
                                  artist=artist, release=release))

        return recording_list
