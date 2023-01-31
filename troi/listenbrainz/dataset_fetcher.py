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

    def __init__(self, server_url, json_post_data, max_num_items=None):
        super().__init__()
        self.server_url = server_url
        self.json_post_data = json_post_data
        self.max_num_items = max_num_items

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording, Artist]

    def create_recording(self, row):

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
            r.listenbrainz = {"listen_count": row["listen_count"]}

        if 'bpm' in row:
            r.acousticbrainz = {"bpm": row["bpm"]}

        return r

    def create_artist(self, row):

        if 'artist_mbid' in row:
            return Artist(mbids=[row['artist_mbid']])

        if 'artist_credit_name' in row:
            return Artist(name=row['artist_credit_name'])

        if 'artist_credit_id' in row:
            return Artist(artist_credit_id=row['artist_credit_id'])

        if 'artist_mbids' in row:
            return Artist(mbids=row['artist_mbids'])

        return None

    def read(self, inputs):

        r = requests.post(self.server_url, json=self.json_post_data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch first dataset recordings from ListenBrainz. HTTP code %s (%s)" %
                                (r.status_code, r.text))

        try:
            data = r.json()[3]["data"]
        except (IndexError, KeyError):
            data = r.json()

        output = []
        for row in data:
            if "recordind_mbid" in row:
                r = self.create_recording(row)
            elif "artist_mbid" in row:
                r = self.create_artist(row)
            else:
                continue

            output.append(r)

        if self.max_num_items is not None:
            output = output[:self.max_num_items]

        return output
