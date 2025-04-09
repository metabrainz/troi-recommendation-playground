import requests
import logging

from collections import defaultdict
from more_itertools import chunked
from .utils import SoundcloudAPI, SoundCloudException

logger = logging.getLogger(__name__)

SOUNDCLOUD_IDS_LOOKUP_URL = "https://labs.api.listenbrainz.org/soundcloud-id-from-mbid/json"

def lookup_soundcloud_ids(recordings):
    """ Given a list of Recording elements, try to find soundcloud track ids from labs api soundcloud lookup using mbids
    and add those to the recordings. """
    response = requests.post(
        SOUNDCLOUD_IDS_LOOKUP_URL,
        json=[{"recording_mbid": recording.mbid} for recording in recordings]
    )
    response.raise_for_status()

    soundcloud_data = response.json()
    mbid_soundcloud_ids_index = {}
    soundcloud_id_mbid_index = {}
    for recording, lookup in zip(recordings, soundcloud_data):
        if len(lookup["soundcloud_track_ids"]) > 0:
            recording.soundcloud_id = lookup["soundcloud_track_ids"][0]
            mbid_soundcloud_ids_index[recording.mbid] = lookup["soundcloud_track_ids"]
            for soundcloud_id in lookup["soundcloud_track_ids"]:
                soundcloud_id_mbid_index[soundcloud_id] = recording.mbid
    return recordings, mbid_soundcloud_ids_index, soundcloud_id_mbid_index


def _check_unplayable_tracks(soundcloud: SoundcloudAPI, playlist_id: str):
    """ Retrieve tracks for given soundcloud playlist and split into lists of playable and unplayable tracks """
    tracks = soundcloud.get_playlist_tracks(playlist_id, linked_partitioning=True, limit=100, access=['playable, preview ,blocked'])
    track_details = [
        {
            "id": track["id"],
            "title": track["title"],
            "access": track["access"]
        }
        for track in tracks
    ]

    playable = []
    unplayable = []
    for idx, item in enumerate(track_details):
        if item["access"] == "playable":
            playable.append((idx, item["id"]))
        else:
            unplayable.append((idx, item["id"]))
    return playable, unplayable


def _get_alternative_track_ids(unplayable, mbid_soundcloud_id_idx, soundcloud_id_mbid_idx):
    """ For the list of unplayable track ids, find alternative tracks ids.

    mbid_soundcloud_id_idx is an index with mbid as key and list of equivalent soundcloud ids as value.
    soundcloud_id_mbid_idx is an index with soundcloud_id as key and the corresponding mbid as value.
    """
    index = defaultdict(list)
    soundcloud_ids = []
    for idx, soundcloud_id in unplayable:
        mbid = soundcloud_id_mbid_idx[str(soundcloud_id)]
        other_soundcloud_ids = mbid_soundcloud_id_idx[mbid]

        for new_idx, new_soundcloud_id in enumerate(other_soundcloud_ids):
            if new_soundcloud_id == soundcloud_id:
                continue
            soundcloud_ids.append(new_soundcloud_id)
            index[idx].append(new_soundcloud_id)
            
    return soundcloud_ids, index


def _get_fixed_up_tracks(soundcloud: SoundcloudAPI, soundcloud_ids, index):
    """ Lookup the all alternative soundcloud track ids, filter playable ones and if multiple track ids
        for same item match, prefer the one occurring earlier. If no alternative is playable, ignore the
        item altogether.
    """
    new_tracks = soundcloud.get_track_details(soundcloud_ids)

    new_tracks_ids = set()
    for item in new_tracks:
        if item["access"] == "playable":
            new_tracks_ids.add(item["id"])

    fixed_up_items = []
    for idx, soundcloud_ids in index.items():
        for soundcloud_id in soundcloud_ids:
            if soundcloud_id in new_tracks_ids:
                fixed_up_items.append((idx, soundcloud_id))
                break
    return fixed_up_items


def fixup_soundcloud_playlist(soundcloud: SoundcloudAPI, playlist_id: str, mbid_soundcloud_id_idx, soundcloud_id_mbid_idx):
    """ Fix unplayable tracks in the given soundcloud playlist.

    Given a soundcloud playlist id, look it up and find unstreamable tracks. If there are any unstreamable tracks, try
    alternative soundcloud track ids from index/reverse_index if available. If alternative is not available or alternatives
    also are unplayable, remove the track entirely from the playlist. Finally, update the playlist if needed.
    """
    playable, unplayable = _check_unplayable_tracks(soundcloud, playlist_id)
    if not unplayable:
        return

    alternative_ids, index = _get_alternative_track_ids(unplayable, mbid_soundcloud_id_idx, soundcloud_id_mbid_idx)
    if not alternative_ids:
        return

    fixed_up = _get_fixed_up_tracks(soundcloud, alternative_ids, index)
    all_items = []
    all_items.extend(playable)
    all_items.extend(fixed_up)

    # sort all items by index value to ensure the order of tracks of original playlist is preserved
    all_items.sort(key=lambda x: x[0])
    # update all track ids the soundcloud playlist
    finalized_ids = [x[1] for x in all_items]

    # clear existing playlist
    soundcloud.update_playlist_details(playlist_id, track_ids=[])

    # chunking requests to avoid hitting rate limits
    for chunk in chunked(finalized_ids, 100):
        soundcloud.add_playlist_tracks(playlist_id, chunk)


def get_tracks_from_soundcloud_playlist(developer_token, playlist_id):
    """ Get tracks from the Soundcloud playlist.
    """
    soundcloud = SoundcloudAPI(developer_token)
    tracks = soundcloud.get_playlist_tracks(playlist_id, linked_partitioning=True, limit=100, access=['playable, preview ,blocked'])

    mapped_tracks = [
        {
            "recording_name": track['title'].split(" - ")[1] if " - " in track['title'] else track['title'],
            "artist_name": track['title'].split(" - ")[0] if " - " in track['title'] else track['user']['username']
        }
        for track in tracks
    ]

    return mapped_tracks


def get_soundcloud_playlist(developer_token, playlist_id):
    soundcloud = SoundcloudAPI(developer_token)
    data = soundcloud.get_playlist(playlist_id)
    name = data["title"]
    description = data["description"]

    if description is None:
        description = ""

    return [], name, description


def submit_to_soundcloud(soundcloud: SoundcloudAPI, playlist, is_public: bool = True,
                         existing_url: str = None):
    """ Submit or update an existing soundcloud playlist.

    If existing urls are specified then is_public and is_collaborative arguments are ignored.
    """
    filtered_recordings = [r for r in playlist.recordings if r.mbid]

    _, mbid_soundcloud_index, soundcloud_mbid_index = lookup_soundcloud_ids(filtered_recordings)
    soundcloud_track_ids = [r.soundcloud_id for r in filtered_recordings if r.soundcloud_id]
    if len(soundcloud_track_ids) == 0:
        return None, None

    logger.info("submit %d tracks" % len(soundcloud_track_ids))

    playlist_id, playlist_url = None, None
    if existing_url:
        # update existing playlist
        playlist_url = existing_url
        playlist_id = existing_url.split("/")[-1]
        try:
            soundcloud.update_playlist_details(playlist_id=playlist_id, title=playlist.name, description=playlist.description)
        except SoundCloudException as err:
            # one possibility is that the user has deleted the soundcloud from playlist, so try creating a new one
            logger.info("provided playlist url has been unfollowed/deleted by the user, creating a new one")
            playlist_id, playlist_url = None, None

    if not playlist_id:
        # create new playlist
        soundcloud_playlist = soundcloud.create_playlist(
            title=playlist.name,
            sharing=is_public,
            description=playlist.description
        )
        playlist_id = soundcloud_playlist["id"]
        playlist_url = soundcloud_playlist["permalink_url"]
    else:
        # existing playlist, clear it
        tracks = map(lambda id: dict(id=id), [0])
        soundcloud.update_playlist(playlist_id, tracks)

    for chunk in chunked(soundcloud_track_ids, 100):
        soundcloud.add_playlist_tracks(playlist_id, chunk)

    fixup_soundcloud_playlist(soundcloud, playlist_id, mbid_soundcloud_index, soundcloud_mbid_index)

    playlist.add_metadata({"external_urls": {"soundcloud": playlist_url}})

    return playlist_url, playlist_id