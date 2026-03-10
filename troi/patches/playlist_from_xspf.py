from troi import Playlist
from troi.patch import Patch
from troi.playlist import RecordingsFromXSPFElement, PlaylistMakerElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.tools.xspf_lookup import parse_xspf


class ImportXSPFPlaylistPatch(Patch):

    @staticmethod
    def inputs():
        """
        A patch that imports an XSPF playlist file into ListenBrainz.

        \b
        XSPF_CONTENT is the raw XML string of the XSPF file.
        """
        return [
            {"type": "argument", "args": ["xspf_content"], "kwargs": {"required": True}},
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "import-xspf-playlist"

    @staticmethod
    def description():
        return "Import an XSPF playlist file into ListenBrainz"

    def create(self, inputs):
        xspf_content = inputs["xspf_content"]

        name, desc, _ = parse_xspf(xspf_content)

        source = RecordingsFromXSPFElement(xspf_content=xspf_content)

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(source)

        pl_maker = PlaylistMakerElement(name, desc, patch_slug=self.slug())
        pl_maker.set_sources(rec_lookup)

        return pl_maker
