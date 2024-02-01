def get_tag_value(tags, tag, default=None):
    """
        Get the tag value and return the first item in the list or None if that is not possible.
    """

    try:
        t = tags[tag]
    except KeyError:
        return default

    return t[0]


def extract_track_number(track_number):
    """
        Parse the various forms of track number formats and return a simple integer. If nothing
        sensible is found, return None
    """

    if track_number is None:
        return None

    # Used for m4a tags
    if isinstance(track_number, tuple):
        return track_number[0]

    # Used for ID3
    if str(track_number).find("/") != -1:
        track_number, dummy = str(track_number).split("/")
    try:
        return_value = int(track_number)
    except ValueError:
        return_value = None

    return return_value


def make_artist_array(artist_id):
    """
        Given artist id tag data, return a string from the data.
        Accepts: list, string. If something else is passed, cast to str.
    """
    if isinstance(artist_id, str):
        return artist_id

    if isinstance(artist_id, list):
        return ",".join(artist_id)

    return str(artist_id)
