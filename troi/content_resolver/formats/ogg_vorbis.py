import mutagen.oggvorbis

from troi.content_resolver.formats.tag_utils import get_tag_value, extract_track_number


EXTENSIONS = {'.ogg'}
READER = mutagen.oggvorbis.OggVorbis


def get_metadata(tags):

    mdata = {}
    mdata["artist_name"] = get_tag_value(tags, "artist")
    mdata["artist_sortname"] = get_tag_value(tags, "artistsort")
    mdata["release_name"] = get_tag_value(tags, "album")
    mdata["recording_name"] = get_tag_value(tags, "title")
    mdata["track_num"] = extract_track_number(get_tag_value(tags, "tracknumber"))
    mdata["disc_num"] = int(get_tag_value(tags, "discnumber") or 1)
    mdata["artist_mbid"] = get_tag_value(tags, "musicbrainz_artistid", "")
    mdata["recording_mbid"] = get_tag_value(tags, "musicbrainz_trackid", "")
    mdata["release_mbid"] = get_tag_value(tags, "musicbrainz_albumid", "")
    mdata["duration"] = int(tags.info.length * 1000)

    return mdata
