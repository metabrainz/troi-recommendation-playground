import mutagen.mp3

from troi.content_resolver.formats.tag_utils import get_tag_value, extract_track_number


EXTENSIONS = {'.mp3', '.mp2', '.m2a'}
READER = mutagen.mp3.MP3


def get_metadata(tags):

    mdata = {}
    if "TPE1" in tags:
        mdata["artist_name"] = str(tags["TPE1"])
    else:
        mdata["artist_name"] = None

    if "TSOP" in tags:
        mdata["sortname"] = str(tags["TSOP"])
    else:
        if "XSOP" in tags:
            mdata["artist_sortname"] = str(tags["XSOP"])
        else:
            mdata["artist_sortname"] = ""

    if "TALB" in tags:
        mdata["release_name"] = str(tags["TALB"])
    else:
        mdata["release_name"] = None

    if "TIT2" in tags:
        mdata["recording_name"] = str(tags["TIT2"])
    else:
        mdata["recording_name"] = None

    if "TRCK" in tags:
        mdata["track_num"] = extract_track_number(str(tags["TRCK"]))
    else:
        mdata["track_num"] = 0

    if "TPOS" in tags:
        mdata["disc_num"] = extract_track_number(str(tags["TPOS"]))
    else:
        mdata["disc_num"] = 1

    if "TXXX:MusicBrainz Artist Id" in tags:
        id = str(tags["TXXX:MusicBrainz Artist Id"])
        # sometimes artist id fields contain two ids. For now, pick the first one and go
        ids = id.split("/")
        mdata["artist_mbid"] = ids[0]
    else:
        mdata["artist_mbid"] = None

    if "UFID:http://musicbrainz.org" in tags:
        mdata["recording_mbid"] = tags["UFID:http://musicbrainz.org"].data.decode("utf-8")
    else:
        mdata["recording_mbid"] = None

    if "TXXX:MusicBrainz Album Id" in tags:
        mdata["release_mbid"] = str(tags["TXXX:MusicBrainz Album Id"])
    else:
        mdata["release_mbid"] = None

    if "TXXX:MusicBrainz Album Artist Id" in tags:
        mdata["release_artist_mbid"] = str(tags["TXXX:MusicBrainz Album Artist Id"])
    else:
        mdata["release_artist_mbid"] = None
    mdata["duration"] = int(tags.info.length * 1000)

    return mdata
