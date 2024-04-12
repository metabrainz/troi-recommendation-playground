import requests
import ujson

from troi import Element, Recording


class MBIDReaderElement(Element):
    '''
        Read MBIDs from a file, one per line and return Recording objects with the MBID field filled out.

        :param filename: The name (with full path) of the file to read recording MBIDs from.
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
