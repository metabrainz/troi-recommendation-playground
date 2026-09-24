from troi.patches.playlist_from_xspf import ImportXSPFPlaylistPatch

SAMPLE_XSPF = """<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
  <title>Soundiiz Export</title>
  <annotation>My road trip playlist</annotation>
  <trackList>
    <track>
      <title>Blue (Da Ba Dee)</title>
      <creator>Eiffel 65</creator>
    </track>
  </trackList>
</playlist>"""


def test_patch_slug_and_description():
    assert ImportXSPFPlaylistPatch.slug() == "import-xspf-playlist"
    assert "XSPF" in ImportXSPFPlaylistPatch.description()


def test_patch_creates_pipeline():
    """create() must wire up the pipeline without raising and return a PlaylistMakerElement."""
    from troi.playlist import PlaylistMakerElement

    args = {
        "xspf_content": SAMPLE_XSPF,
        "token": "test-token",
        "upload": False,
        "created_for": None,
        "echo": False,
        "min_recordings": 1,
    }
    patch = ImportXSPFPlaylistPatch(args)
    result = patch.create(args)

    assert isinstance(result, PlaylistMakerElement)
    # The playlist name and description must come from the XSPF, not be hardcoded
    assert result.name == "Soundiiz Export"
    assert result.desc == "My road trip playlist"
