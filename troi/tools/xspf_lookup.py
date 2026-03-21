import re
import html
from xml.etree import ElementTree as ET
from troi.playlist import PLAYLIST_TRACK_URI_PREFIX

XSPF_NS = "http://xspf.org/ns/0/"


def _fix_entities(text: str) -> str:
    """Clean up Soundiiz-style double-escaped HTML entities."""
    text = re.sub(r"<(#?\w+);", r"&\1;", text)
    return html.unescape(text)


def parse_xspf(xspf_content: str):
    """Parse XSPF XML content.

    Returns:
        tuple: (name, description, tracks)
            name (str): playlist title, defaults to "Untitled Playlist"
            description (str): playlist annotation, defaults to ""
            tracks (list[dict]): each dict has:
                - recording_name (str)
                - artist_name (str)
                - isrc (str, optional) — present when <isrc> is in the file;
                  stored for future use, not currently used for MBID resolution
                - recording_mbid (str, optional) — only set when <identifier>
                  contains a MusicBrainz recording URI; absent in most
                  real-world XSPF files (e.g. Soundiiz exports)
    """
    root = ET.fromstring(xspf_content)

    name = root.findtext(f"{{{XSPF_NS}}}title") or "Untitled Playlist"
    description = root.findtext(f"{{{XSPF_NS}}}annotation") or ""

    tracks = []
    track_list = root.find(f"{{{XSPF_NS}}}trackList")
    if track_list is None:
        return name, description, tracks

    for track in track_list.findall(f"{{{XSPF_NS}}}track"):
        recording_name = _fix_entities(track.findtext(f"{{{XSPF_NS}}}title") or "")
        artist_name = _fix_entities(track.findtext(f"{{{XSPF_NS}}}creator") or "")

        track_data = {
            "recording_name": recording_name,
            "artist_name": artist_name,
        }

        isrc = track.findtext(f"{{{XSPF_NS}}}isrc")
        if isrc:
            track_data["isrc"] = isrc

        # findtext() with a bare tag name only searches direct children of <track>,
        # so nested artist <identifier> elements inside <extension> are never picked up.
        identifier = track.findtext(f"{{{XSPF_NS}}}identifier")
        if identifier and identifier.startswith(PLAYLIST_TRACK_URI_PREFIX):
            track_data["recording_mbid"] = identifier[len(PLAYLIST_TRACK_URI_PREFIX):]

        tracks.append(track_data)

    return name, description, tracks
