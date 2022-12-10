import troi
from troi import Recording
from troi.musicbrainz.mbid_reader import MBIDReaderElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.playlist import PlaylistMakerElement


class PlaylistFromMBIDsPatch(troi.patch.Patch):
    """
    """

    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    def get_args():
        return [
            {
                "type": "argument",
                "args": ["file_name"],
                "kwargs": {}
            }
        ]

    @staticmethod
    def get_documentation():
        return """
        Make a playlist from a file containing one MBID per line.

        \b
        FILE_NAME: filename that contains MBIDS
        """

    @staticmethod
    def inputs():
        return [{"type": str, "name": "file_name", "desc": "MBID filename", "optional": False}]

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
