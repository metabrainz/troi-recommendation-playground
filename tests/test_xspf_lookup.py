from troi.tools.xspf_lookup import parse_xspf

# Real Soundiiz export shape: no <identifier>, has <isrc>, malformed entities
XSPF_SOUNDIIZ = """<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
  <title>My Soundiiz Playlist</title>
  <trackList>
    <track>
      <title>Pink Venom</title>
      <creator>BLACKPINK</creator>
      <album>Pink Venom</album>
      <isrc>KRA402200017</isrc>
    </track>
    <track>
      <title>I Ain&lt;#039;t Worried</title>
      <creator>OneRepublic</creator>
      <isrc>USUM72206227</isrc>
    </track>
    <track>
      <title>Bad Decisions (with BTS &lt;amp; Snoop Dogg)</title>
      <creator>benny blanco, BTS, Snoop Dogg</creator>
      <isrc>USUM72210832</isrc>
    </track>
  </trackList>
</playlist>"""

# LB XSPF export shape: recording <identifier> + nested artist identifiers + annotation
XSPF_LB_EXPORT = """<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
  <title>Top discoveries</title>
  <identifier>https://listenbrainz.org/playlist/862add71-2e87-44b7-abe1-a7f1a8658346</identifier>
  <annotation>&lt;p&gt;Some description&lt;/p&gt;</annotation>
  <extension application="https://musicbrainz.org/doc/jspf#playlist">
    <public>true</public>
    <creator>chaban</creator>
  </extension>
  <trackList>
    <track>
      <identifier>https://musicbrainz.org/recording/85701f84-c37f-4857-89d3-29625f02d943</identifier>
      <creator>Frozen Starfall feat. Milkychan</creator>
      <album>Mirrored Worlds</album>
      <title>Inner Storm</title>
      <extension application="https://musicbrainz.org/doc/jspf#track">
        <added_by>troi-bot</added_by>
        <artist_identifiers>
          <identifier>https://musicbrainz.org/artist/e4b67829-4010-4420-8d13-125266683b77</identifier>
        </artist_identifiers>
      </extension>
    </track>
    <track>
      <identifier>https://example.com/not-a-mb-uri</identifier>
      <creator>Darude</creator>
      <title>Sandstorm</title>
    </track>
  </trackList>
</playlist>"""


def test_parse_soundiiz_xspf():
    """Full parse of a Soundiiz-style export: entity cleanup, ISRC extraction, no MBIDs."""
    name, description, tracks = parse_xspf(XSPF_SOUNDIIZ)

    assert name == "My Soundiiz Playlist"
    assert description == ""
    assert len(tracks) == 3

    assert tracks[0] == {"recording_name": "Pink Venom", "artist_name": "BLACKPINK", "isrc": "KRA402200017"}
    assert tracks[1] == {"recording_name": "I Ain't Worried", "artist_name": "OneRepublic", "isrc": "USUM72206227"}
    assert tracks[2] == {"recording_name": "Bad Decisions (with BTS & Snoop Dogg)",
                         "artist_name": "benny blanco, BTS, Snoop Dogg", "isrc": "USUM72210832"}


def test_parse_lb_xspf_roundtrip():
    """Full parse of an LB XSPF export: recording MBIDs, annotation, non-MB identifiers ignored,
    nested artist identifiers not confused with recording identifier."""
    name, description, tracks = parse_xspf(XSPF_LB_EXPORT)

    assert name == "Top discoveries"
    assert description == "<p>Some description</p>"  # LB uses correct XML escaping
    assert len(tracks) == 2

    # Track with MB recording URI: MBID extracted directly
    assert tracks[0]["recording_name"] == "Inner Storm"
    assert tracks[0]["artist_name"] == "Frozen Starfall feat. Milkychan"
    assert tracks[0]["recording_mbid"] == "85701f84-c37f-4857-89d3-29625f02d943"
    assert "isrc" not in tracks[0]

    # Track with non-MB identifier: recording_mbid must be absent, falls through to name resolution
    assert tracks[1]["recording_name"] == "Sandstorm"
    assert "recording_mbid" not in tracks[1]


def test_parse_empty_xspf():
    """Empty trackList and missing optional fields produce safe defaults."""
    xspf = """<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/"><trackList/></playlist>"""

    name, description, tracks = parse_xspf(xspf)
    assert name == "Untitled Playlist"
    assert description == ""
    assert tracks == []
