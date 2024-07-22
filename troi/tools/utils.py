import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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

    def _assert_status_hook(response, *args, **kwargs):
        response.raise_for_status()

    http.hooks["response"] = [_assert_status_hook]

    return http