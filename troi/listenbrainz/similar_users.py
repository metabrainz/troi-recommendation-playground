import requests
import ujson

from troi import Element, Recording, User


class SimilarUserLookupElement(Element):
    """
        Look up musicbrainz tag and genres for a list of recordings recordings, based on recording mbid.
    """

    SERVER_URL = "https://api.listenbrainz.org/1/%s/similar-users"

    def __init__(self, user_name):
        Element.__init__(self)
        self.user_name = user_name

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [User]

    def read(self, inputs):

        r = requests.get(self.SERVER_URL % self.user_name)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch recording tags from MusicBrainz: HTTP code %d" % r.status_code)

        return r.json()["payload"]
