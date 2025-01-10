import requests
import json
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
SOUNDCLOUD_URL = f"https://api.soundcloud.com/"
APPLE_MUSIC_URL = f"https://api.music.apple.com/v1"

class AppleMusicException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(f"Apple Music api error {code}: {msg}")


class AppleMusicAPI:
    def __init__(self, developer_token, user_token):
        self.developer_token = developer_token
        self.user_token = user_token
        self.headers = {
            "Authorization": f"Bearer {self.developer_token}",
            "Music-User-Token": self.user_token,
            "Content-Type": "application/json"
        }
        self.session = create_http_session()
        self.storefront = self._get_user_storefront()

    def _get_user_storefront(self):
        """ Fetch a storefront for a specific user.
        """
        url=f"{APPLE_MUSIC_URL}/me/storefront"
        response = self.session.get(url, headers=self.headers)

        data = response.json()["data"][0]["id"]
        return data

    def create_playlist(self, name, is_public=True,description=None):
        url = f"{APPLE_MUSIC_URL}/me/library/playlists"
        data = {
            "attributes": {
                "name": name,
                "isPublic": is_public
            }
        }
        if description:
            data["attributes"]["description"] = description
        response = self.session.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def playlist_add_tracks(self, playlist_id, track_ids):
        """ Adds tracks to a playlist in Apple Music, does not return response
        """
        url = f"{APPLE_MUSIC_URL}/me/library/playlists/{playlist_id}/tracks"
        data = {
            "data": [{"id": track_id, "type": "songs"} for track_id in track_ids]
        }
        self.session.post(url, headers=self.headers, data=json.dumps(data))

    def get_playlist_tracks(self, playlist_id):
        url = f"{APPLE_MUSIC_URL}/me/library/playlists/{playlist_id}?include=tracks"
        response = self.session.get(url, headers=self.headers).json()
        tracks = response["data"][0]["relationships"]["tracks"]["data"]
        total_tracks_count = response["data"][0]["relationships"]["tracks"]["meta"]["total"]
        playlist_name = response["data"][0]["attributes"]["name"]
        playlist_description = response["data"][0]["attributes"].get(
            "description", {}).get("standard", "")

        # apple music returns only the first 100 tracks with "/playlists/{playlist_id}?include=tracks"
        # and we need to fetch the rest of the tracks using the "playlists/{playlist_id}/tracks" endpoint
        if len(tracks) < total_tracks_count:
            offset = len(tracks)
            # endpoint returns 100 tracks per call max -> run iteratively with an offset until there are no more tracks
            while True:
                url = f"{APPLE_MUSIC_URL}/me/library/playlists/{playlist_id}/tracks?limit=100&offset={offset}"
                response = self.session.get(url, headers=self.headers).json()
                try:
                    if "errors" in response:
                        # https: // developer.apple.com/documentation/applemusicapi/errorsresponse
                        error_objects = response["errors"]
                        for error_object in error_objects:
                            error_message = error_object["detail"] if "detail" in error_object else error_object["title"]
                            logger.error(
                                f"Error code {error_object['status']}: {error_message}")
                        break

                    tracks_data = response["data"]
                    tracks.extend(tracks_data) if tracks_data else None

                    if len(tracks_data) == 0 or len(tracks) == total_tracks_count:
                        break
                    # set new offset for the next loop
                    offset = offset + len(tracks_data)
                except KeyError as err:
                    # No data returned from API call, could be an error, do nothing
                    logger.error(
                        "Failed to fetch Apple playlist tracks: %s, ignoring error..." % err)
                    break

        return tracks, playlist_name, playlist_description


class SoundCloudException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(f"http error {code}: {msg}")


class SoundcloudAPI:
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"OAuth {self.access_token}",
            "Content-Type": "application/json"
        }
        self.session = create_http_session()

    def create_playlist(self, title, sharing="public", track_ids=None, description=None):
        url = f"{SOUNDCLOUD_URL}/playlists"
        data = {
            "playlist": {
                "title": title,
                "sharing": sharing,
            }
        }
        if track_ids:
            data["playlist"]["tracks"] = [{"id": track_id} for track_id in track_ids]

        if description:
            data["playlist"]["description"] = description
        response = self.session.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def add_playlist_tracks(self, playlist_id, track_ids):
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}"
        data = {
            "playlist": {
                "tracks": [{"id": track_id} for track_id in track_ids]
            }
        }
        response = self.session.put(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def update_playlist_details(self, playlist_id, title=None, description=None, track_ids=None):
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}"
        data = {
            "playlist": {}
        }
        if title:
            data["playlist"]["title"] = title
        if description:
            data["playlist"]["description"] = description
        if track_ids:
            data["playlist"]["tracks"] = [{"id": track_id} for track_id in track_ids]

        response = self.session.put(url, headers=self.headers, data=json.dumps(list(data)))
        return response.json()

    def get_track_details(self, track_ids):
        track_details = []

        for track_id in track_ids:
            url = f"{SOUNDCLOUD_URL}/tracks/{track_id}"
            response = self.session.get(url, headers=self.headers)
            data = response.json()
            track_details.append(data)

        return track_details


    def get_playlist(self, playlist_id):
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}"

        response = self.session.get(url, headers=self.headers)
        return response.json()


    def get_playlist_tracks(self, playlist_id, **kwargs):
        tracks = []
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}/tracks"

        while url:
            response = self.session.get(url, headers=self.headers, params=kwargs)
            data = response.json()
            tracks.extend(data.get('collection', []))
            url = data.get("next_href")

        return tracks


def create_http_session():
    """ Create an HTTP session with retry strategy for handling rate limits and server errors.
    """
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http
