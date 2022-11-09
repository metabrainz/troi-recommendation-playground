from collections import defaultdict

import requests
import spotipy

SPOTIFY_IDS_LOOKUP_URL = "https://labs.api.listenbrainz.org/spotify-id-from-mbid/json"


def lookup_spotify_ids(recordings):
    """ Given a list of Recording elements, try to find spotify track ids from labs api spotify lookup using mbids
    and add those to the recordings. """
    response = requests.post(
        SPOTIFY_IDS_LOOKUP_URL,
        json=[{"[recording_mbid]": recording.mbid} for recording in recordings]
    )
    response.raise_for_status()
    spotify_data = response.json()
    mbid_spotify_ids_index = {}
    spotify_id_mbid_index = {}
    for recording, lookup in zip(recordings, spotify_data):
        if len(lookup["spotify_track_ids"]) > 0:
            recording.spotify_id = lookup["spotify_track_ids"][0]
            mbid_spotify_ids_index[recording.mbid] = lookup["spotify_track_ids"]
            for spotify_id in lookup["spotify_track_ids"]:
                spotify_id_mbid_index[spotify_id] = recording.mbid
    return recordings, mbid_spotify_ids_index, spotify_id_mbid_index


def _check_unplayable_tracks(sp: spotipy.Spotify, playlist_id: str):
    """ Retrieve tracks for given spotify playlist and split into lists of playable and unplayable tracks """
    playlist = sp.playlist_items(playlist_id, fields="items(track(name,id,is_playable))", market="from_token")
    playable = []
    unplayable = []
    for idx, item in enumerate(playlist["items"]):
        if item["track"]["is_playable"]:
            playable.append((idx, item["track"]["id"]))
        else:
            unplayable.append((idx, item["track"]["id"]))
    return playable, unplayable


def _get_alternative_track_ids(unplayable, mbid_spotify_id_idx, spotify_id_mbid_idx):
    """ For the list of unplayable track ids, find alternative tracks ids.

    mbid_spotify_id_idx is an index with mbid as key and list of equivalent spotify ids as value.
    spotify_id_mbid_idx is an index with spotify_id as key and the corresponding mbid as value.
    """
    index = defaultdict(list)
    spotify_ids = []
    
    for idx, spotify_id in unplayable:
        mbid = spotify_id_mbid_idx[spotify_id]
        other_spotify_ids = mbid_spotify_id_idx[mbid]

        for new_idx, new_spotify_id in enumerate(other_spotify_ids):
            if new_spotify_id == spotify_id:
                continue
            spotify_ids.append(new_spotify_id)
            index[idx].append(new_spotify_id)
            
    return spotify_ids, index


def _get_fixed_up_tracks(sp: spotipy.Spotify, spotify_ids, index):
    """ Lookup the all alternative spotify track ids, filter playable ones and if multiple track ids
        for same item match, prefer the one occurring earlier. If no alternative is playable, ignore the
        item altogether.
    """
    new_tracks = sp.tracks(spotify_ids, market="from_token")
    new_tracks_ids = set()
    for item in new_tracks["tracks"]:
        if item["is_playable"]:
            new_tracks_ids.add(item["id"])

    fixed_up_items = []
    for idx, spotify_ids in index.items():
        for spotify_id in spotify_ids:
            if spotify_id in new_tracks_ids:
                fixed_up_items.append((idx, spotify_id))
                break

    return fixed_up_items


def fixup_spotify_playlist(sp: spotipy.Spotify, playlist_id: str, mbid_spotify_id_idx, spotify_id_mbid_idx):
    """ Fix unplayable tracks in the given spotify playlist.

    Given a spotify playlist id, look it up and find unplayable tracks. If there are any unplayable tracks, try
    alternative spotify track ids from index/reverse_index if available. If alternative is not available or alternatives
    also are unplayable, remove the track entirely from the playlist. Finally, update the playlist if needed.
    """
    playable, unplayable = _check_unplayable_tracks(sp, playlist_id)
    if not unplayable:
        return

    alternative_ids, index = _get_alternative_track_ids(unplayable, mbid_spotify_id_idx, spotify_id_mbid_idx)
    if not alternative_ids:
        return

    fixed_up = _get_fixed_up_tracks(sp, alternative_ids, index)
    all_items = []
    all_items.extend(playable)
    all_items.extend(fixed_up)

    # sort all items by index value to ensure the order of tracks of original playlist is preserved
    all_items.sort(key=lambda x: x[0])
    # update all track ids the spotify playlist
    finalized_ids = [x[1] for x in all_items]
    result = sp.playlist_replace_items(playlist_id, finalized_ids)
