import requests
import json
import logging
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
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
        self.session = self._create_http_session()
        self.storefront = self._get_user_storefront()
    
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

        def raise_for_status_hook(response, *args, **kwargs):
            try:
                response.raise_for_status()
            except HTTPError as http_err:
                logger.error(f"HTTP error occurred: {http_err}")
                raise

        http.hooks["response"] = [raise_for_status_hook]
        return http

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
        response = self.session.post(url, headers=self.headers, data=json.dumps(data))

    
    def get_track_details(self, track_ids):
        track_details = []
        for track_id in track_ids:
            url = f"{APPLE_MUSIC_URL}/catalog/{self.storefront}/songs/{track_id}"
            response = self.session.get(url, headers=self.headers)
            data = response.json()
            track_details.append(data)
        return track_details

    def get_playlist_tracks(self, playlist_id):
        url = f"{APPLE_MUSIC_URL}/me/library/playlists/{playlist_id}?include=tracks"
        response = self.session.get(url, headers=self.headers)
        return response.json()


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
