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
        return [Playlist]

    def read(self, inputs):

        r = requests.post(self.server_url, json=self.json_post_data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch first dataset recordings from ListenBrainz. HTTP code %s" % r.status_code)

        recordings = []
        for row in r.json():
            if row['recording_mbid'] is None:
                continue

            recordings.append(Recording(mbid=row['recording_mbid'], 
                                        name=row['recording_name'], 
                                        listenbrainz={"listen_count": row["listen_count"]},
                                        artist=Artist(name=row['artist_credit_name'])))

            self.debug("%-60s %-50s %d" % (row['recording_name'][:59], row['artist_credit_name'][:49], row["listen_count"]))

        return recordings
