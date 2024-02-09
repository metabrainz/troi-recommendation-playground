import os

from troi.logging import info
from troi.splitter import plist
from troi import Recording as TroiRecording
from troi.content_resolver.model.recording import FileIdType


def ask_yes_no_question(prompt):

    while True:
        resp = input(prompt)
        resp = resp.strip()
        if resp == "":
            resp = 'y'

        if resp == 'y':
            return True
        elif resp == 'n':
            return False
        else:
            info("eh? try again.")


def select_recordings_on_popularity(recordings, begin_percent, end_percent, num_recordings):
    """
       Given dicts of recording data, select up to num_recordings recordings randomly
       from the recordings that ideally lie in popularity between begin_percent and end_percent.

       If too little data is found in the percent range, select recordings that are the closest
       to the disired range.
    """

    matching_recordings = []
    over_recordings = []
    under_recordings = []
    for rec in recordings:
        if rec["popularity"] >= begin_percent:
            if rec["popularity"] < end_percent:
                matching_recordings.append(rec)
            else:
                over_recordings.append(rec)
        else:
            under_recordings.append(rec)

    # If we have enough recordings, skip the extending part
    if len(matching_recordings) < num_recordings:
        # We don't have enough recordings, see if we can pick the ones outside
        # of our desired range in a best effort to make a playlist.
        # Keep adding the best matches until we (hopefully) get our desired number of recordings
        while len(matching_recordings) < num_recordings:
            if under_recordings:
                under_diff = begin_percent - under_recordings[-1]["popularity"]
            else:
                under_diff = None

            if over_recordings:
                over_diff = over_recordings[-1]["popularity"] - end_percent
            else:
                over_diff = None

            if over_diff == None and under_diff == None:
                break

            if over_diff is not None and under_diff is not None and under_diff < over_diff:
                matching_recordings.insert(0, under_recordings.pop(-1))
            else:
                if under_diff is not None:
                    matching_recordings.insert(len(matching_recordings), under_recordings.pop(-1))
                else:
                    matching_recordings.insert(len(matching_recordings), over_recordings.pop(0))

    # Convert results into recordings
    results = plist()
    for rec in matching_recordings:
        r = TroiRecording(mbid=rec["recording_mbid"])
        if rec["file_id_type"] == FileIdType.SUBSONIC_ID:
            r.musicbrainz = {"subsonic_id": rec["file_id"]}
        if rec["file_id_type"] == FileIdType.FILE_PATH:
            r.musicbrainz = {"filename": rec["file_id"]}

        results.append(r)

    return results


class bcolors:
    """ Basic ASCII color codes """

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def existing_dirs(paths):
    """Yield absolute paths for all existing directories in the iterable passed"""
    for path in paths:
        abspath = os.path.abspath(path)
        if os.path.isdir(abspath):
            yield abspath
