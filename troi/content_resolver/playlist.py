import json

from troi.playlist import _deserialize_from_jspf, PlaylistElement


def read_jspf_playlist(jspf_file):
    """
        Read a JSPF playlist from disk.
    """

    with open(jspf_file, "r") as f:
        jspf = f.read()

    playlist = _deserialize_from_jspf(json.loads(jspf))
    playlist_element = PlaylistElement()
    playlist_element.playlists = [ playlist ]

    return playlist_element


def write_jspf_playlist(jspf_file, jspf):
    """
        Write a JSPF playlist to disk.
    """

    with open(jspf_file, "w") as f:
        f.write(json.dumps(jspf.get_jspf()))


def write_m3u_playlist(file_name, playlist_element):
    """
       Given a Troi playlist, write an m3u playlist to disk.
    """

    playlist = playlist_element.playlists[0]
    with open(file_name, "w") as m3u:
        m3u.write("#EXTM3U\n")
        m3u.write("#EXTENC: UTF-8\n")
        m3u.write("#PLAYLIST %s\n" % playlist.name)
        for rec in playlist.recordings:
            if rec is None:
                continue
            if rec.duration is None:
                duration = 0
            else: 
                duration = rec.duration / 1000
            m3u.write("#EXTINF %d,%s\n" % (duration, rec.name))
            m3u.write(rec.musicbrainz["filename"] + "\n")
