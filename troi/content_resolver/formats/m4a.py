import mutagen.mp4

from troi.content_resolver.formats.tag_utils import get_tag_value, extract_track_number


EXTENSIONS = {'.m4a', '.m4b', '.m4p', '.m4v', '.m4r', '.mp4'}
READER = mutagen.mp4.MP4


def get_metadata(tags):

    mdata = {}
    mdata["artist_name"] = get_tag_value(tags, "©ART")
    mdata["artist_sortname"] = get_tag_value(tags, "soar", mdata["artist_name"])
    mdata["release_name"] = get_tag_value(tags, "©alb")
    mdata["recording_name"] = get_tag_value(tags, "©nam")
    mdata["track_num"] = extract_track_number(get_tag_value(tags, "trkn"))
    mdata["disc_num"] = get_and_decode(tags, "----:com.apple.iTunes:DISCSUBTITLE")
    mdata["artist_mbid"] = get_and_decode(tags, "----:com.apple.iTunes:MusicBrainz Artist Id")
    mdata["recording_mbid"] = get_and_decode(tags, "----:com.apple.iTunes:MusicBrainz Track Id")
    mdata["release_mbid"] = get_and_decode(tags, "----:com.apple.iTunes:MusicBrainz Album Id")
    mdata["duration"] = int(tags.info.length * 1000)

    return mdata


def get_and_decode(tags, tag_name):
    tag_value = get_tag_value(tags, tag_name)
    if tag_value is not None:
        tag_value = tag_value.decode("utf-8")
    return tag_value
