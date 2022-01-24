import requests

from troi import Element, Artist, Recording, Playlist, PipelineError


class DataSetFetcherElement(Element):
    '''
        Fetch a dataset from the dataset hoster that contains at least a recording_mbid,
        but also recording_name, listen_count and artist_credit_name if the fields
        are available.

        Args:
            server_url: the URL to POST to
            json_post_data: the dict data that will be POSTed as JSON
    '''

    def __init__(self, server_url, json_post_data):
        super().__init__()
        self.server_url = server_url
        self.json_post_data = json_post_data

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        r = requests.post(self.server_url, json=self.json_post_data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch first dataset recordings from ListenBrainz. HTTP code %s" % r.status_code)

        recordings = []
        for row in r.json():
            if row['recording_mbid'] is None:
                continue

            r = Recording(mbid=row['recording_mbid']) 
            if 'artist_credit_name' in row:
                if 'artist_credit_id' in row:
                    r.artist.artist_credit_id = row['artist_credit_id']

            artist = None
            if 'artist_credit_name' in row:
                artist = Artist(name=row['artist_credit_name'])

            if 'artist_credit_id' in row:
                if artist is None:
                    artist = Artist(artist_credit_id=row['artist_credit_id'])
                else:
                    artist.artist_credit_id = row['artist_credit_id']

            if 'artist_mbids' in row:
                if artist is None:
                    artist = Artist(mbids=row['artist_mbids'])
                else:
                    artist.mbids = row['artist_mbids']

            r.artist = artist

            if 'recording_name' in row:
                r.name = row['recording_name']

            if 'year' in row:
                r.year = row['year']

            if 'listen_count' in row:
                r.listenbrainz={"listen_count": row["listen_count"]}

            if 'bpm' in row:
                r.acousticbrainz={"bpm": row["bpm"]}

            recordings.append(r)

        return recordings
