import requests
import ujson

from troi import Element, Artist, PipelineError, Recording


class MBIDReaderElement(Element):
    '''
        Look up a musicbrainz data for a list of recordings, based on MBID.
    '''

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    @staticmethod
    def inputs():
        return [ ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs):

        mbids = []
        with open(self.filename, "r") as f:
            for line in f.readlines():
                if not line:
                    break

                mbid = line.strip()
                mbids.append(Recording(mbid=mbid))

        return mbids
