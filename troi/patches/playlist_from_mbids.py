import troi
from troi import Recording
from troi.musicbrainz.mbid_reader import MBIDReaderElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.patch import Patch
from troi.playlist import PlaylistMakerElement


class PlaylistFromMBIDsPatch(Patch):
    """
    """

    def __init__(self, args):
        super().__init__(args)

    @staticmethod
    def inputs():
        """
        Make a playlist from a file containing one MBID per line.

        \b
        FILE_NAME: filename that contains MBIDS
        """
        return [{"type": "argument", "args": ["file_name"]}]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "playlist-from-mbids"

    @staticmethod
    def description():
        return "Generate a playlist from a list of MBIDSs"

    def create(self, inputs):

        source = MBIDReaderElement(inputs['file_name'])

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(source)

        pl_maker = PlaylistMakerElement("Playlist made from MBIDs", "", patch_slug=self.slug())
        pl_maker.set_sources(rec_lookup)

        return pl_maker
