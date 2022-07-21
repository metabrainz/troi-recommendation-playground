import requests
import json

from troi import Element, Recording, PipelineError

MAX_MBIDS_PER_CALL = 20


class GenreLookupElement(Element):
    """
        Look up musicbrainz tag and genres for a list of recordings recordings, based on recording mbid.
    """

    SERVER_URL = "https://api.listenbrainz.org/1/metadata/recording"
#/?recording_mbids=e97f805a-ab48-4c52-855e-07049142113d&inc=tag

    def __init__(self, count_threshold=3):
        Element.__init__(self)
        self.count_threshold = count_threshold

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]
        if not recordings:
            return []

        mbid_sets = []
        mbids = []
        for r in recordings:
            mbids.append(r.mbid)
            if len(mbids) >= MAX_MBIDS_PER_CALL:
                mbid_sets.append(mbids)
                mbids = []

        output = []

        data = {}
        for mbid_set in mbid_sets:
            r = requests.get(self.SERVER_URL, params={ "recording_mbids" : ",".join(mbid_set), "inc": "tag" })
            if r.status_code != 200:
                raise PipelineError("Cannot fetch tags from ListenBrainz: HTTP code %d" % r.status_code)

            data = {**data, **r.json()}

        for r in recordings:

            if r.mbid not in data:
                continue

            # Save the whole MB metadata tag info
            r.musicbrainz["tag_metadata"] = data[r.mbid]["tag"]


            genres = []
            for genre in data[r.mbid]["tag"]["recording"]:
                if genre["count"] >= self.count_threshold:
                    genres.append(genre["tag"])

            r.musicbrainz["genres"] = genres

            artist_genres = []
            for genre in data[r.mbid]["tag"]["artist"]:
                if genre["count"] >= self.count_threshold:
                    artist_genres.append(genre["tag"])

            r.artist.musicbrainz["genres"] = artist_genres

            output.append(r)

        return output
