from unittest.mock import patch

# one track with MBID (used directly), one without (needs resolution)
XSPF_MIXED = """<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
  <title>Mixed</title>
  <trackList>
    <track>
      <identifier>https://musicbrainz.org/recording/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa</identifier>
      <title>Inner Storm</title>
      <creator>Frozen Starfall</creator>
    </track>
    <track>
      <title>Sandstorm</title>
      <creator>Darude</creator>
    </track>
  </trackList>
</playlist>"""


def test_recordings_from_xspf_mixed():
    """Track with MBID used directly; track without MBID resolved via API. No double-resolution."""
    from troi.playlist import RecordingsFromXSPFElement

    with patch("troi.tools.common_lookup.mbid_mapping_tracks", return_value=["dddddddd-dddd-dddd-dddd-dddddddddddd"]) as mock_mapping:
        element = RecordingsFromXSPFElement(XSPF_MIXED)
        recordings = element.read([])

        # Only the one track without MBID goes to the lookup API
        submitted = [t for batch in mock_mapping.call_args[0][0] for t in batch]
        assert submitted == [{"recording_name": "Sandstorm", "artist_name": "Darude"}]

    mbids = {r.mbid for r in recordings}
    assert "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" in mbids
    assert "dddddddd-dddd-dddd-dddd-dddddddddddd" in mbids
    assert len(recordings) == 2
