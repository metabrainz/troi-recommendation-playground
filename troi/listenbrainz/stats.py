
import requests
import ujson
from troi import Element, Artist, Release, Recording
import pylistenbrainz


class UserArtistsElement(Element):
    '''
        Fetch artist statistics from ListenBrainz
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time'):
        Element.__init__(self)
        self.client = pylistenbrainz.ListenBrainz()
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Artist]

    def read(self, inputs = [], debug=False):

        artist_list = []
        artists = self.client.get_user_artists(self.user_name, self.count, self.offset, self.time_range)
        for a in artists['payload']['artists']:
            artist_list.append(Artist(a['artist_name'], mbids=a['artist_mbids'], msid=a['artist_msid']))

        return artist_list


class UserReleasesElement(Element):
    '''
        Fetch release statistics from ListenBrainz
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time'):
        Element.__init__(self)
        self.client = pylistenbrainz.ListenBrainz()
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Release]

    def read(self, inputs = [], debug=False):

        release_list = []
        releases = self.client.get_user_releases(self.user_name, self.count, self.offset, self.time_range)
        for r in releases['payload']['releases']:
            artist = Artist(r['artist_name'], mbids=r['artist_mbids'], msid=r['artist_msid'])
            release_list.append(Release(r['release_name'], mbid=r['release_mbid'], msid=r['release_msid'], 
                                artist=artist))

        return release_list


class UserRecordingElement(Element):
    '''
        Fetch recording statistics from ListenBrainz
    '''

    def __init__(self, user_name, count=25, offset=0, time_range='all_time'):
        Element.__init__(self)
        self.client = pylistenbrainz.ListenBrainz()
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.time_range = time_range

    def outputs(self):
        return [Recording]

    def read(self, inputs = [], debug=False):
        recording_list = []
        recordings = self.client.get_user_recordings(self.user_name, self.count, self.offset, self.time_range)
        for r in recordings['payload']['recordings']:
            artist = Artist(r['artist_name'], mbids=r['artist_mbids'], msid=r['artist_msid'])
            release = Release(r['release_name'], mbid=r['release_mbid'], msid=r['release_msid'])
            recording_list.append(Recording(r['track_name'], mbid=r['recording_mbid'], msid=r['recording_msid'], 
                                  artist=artist, release=release))

        return recording_list
