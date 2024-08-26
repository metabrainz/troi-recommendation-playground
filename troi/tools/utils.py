import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
        response = self.session.get(url, headers=self.headers)
        return response.json()

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
        self.session = self._create_http_session()

    def _create_http_session(self):
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

    def create_playlist(self, title, sharing="public" ,track_ids=None, description=None):
        url = f"{SOUNDCLOUD_URL}/playlists"
        data = {
            "playlist": {
                "title": title,
                "sharing": sharing
            }
        }
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

    def update_playlist_details(self, playlist_id, title=None, description=None):
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}"
        data = {
            "playlist": {}
        }
        if title:
            data["playlist"]["title"] = title
        if description:
            data["playlist"]["description"] = description

        response = self.session.put(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def get_track_details(self, track_ids, **kwargs):
        track_details = []

        for track_id in track_ids:
            url = f"{SOUNDCLOUD_URL}/tracks/{track_id}"
            response = self.session.get(url, headers=self.headers, params=kwargs)

            if response.status_code != 200:
                track_details.append({
                    "id": track_id,
                    "title": None,
                    "playable": False
                })
                continue

            data = response.json()
            while data.get("collection"):
                track_data = data["collection"][0]
                track_details.append({
                    "id": track_data["id"],
                    "title": track_data["title"],
                    "playable": track_data.get("streamable", True)
                })

                next_href = data.get("next_href")
                if not next_href:
                    break

                data = self.session.get(next_href, headers=self.headers).json()

        return track_details

    def get_playlist_tracks(self, playlist_id, **kwargs):
        tracks = []
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}/tracks"

        while url:
            response = self.session.get(url, headers=self.headers, params=kwargs)
            response.raise_for_status()
            data = response.json()
            tracks.extend(data.get("collection", []))
            url = data.get("next_href")

        print(tracks)
        return tracks

    def get_unplayable_tracks(self, playlist_id, **kwargs):
        unplayable_tracks = []
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}/tracks"

        while url:
            response = self.session.get(url, headers=self.headers, params=kwargs)
            response.raise_for_status()
            data = response.json()

            for track in data.get("collection", []):
                if not track.get("streamable", True):
                    unplayable_tracks.append(track)

            url = data.get("next_href")
        return unplayable_tracks

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
