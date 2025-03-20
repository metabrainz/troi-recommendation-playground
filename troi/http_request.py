import requests
from time import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from icecream import ic

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504, 503, 419),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def http_get(url, headers=None, params=None, **kwargs):

    if not headers:
        headers = {}
    headers["User-Agent"] = "ListenBrainz Troi (rob@meb)"

    session = requests_retry_session()
    while True:
        # Switch back to session!
        r = requests.get(url, params=params, headers=headers, **kwargs)
        print("X-RateLimit-Limit    ", r.headers["X-RateLimit-Limit"])
        print("X-RateLimit-Remaining", r.headers["X-RateLimit-Remaining"])
        print("X-RateLimit-Reset    ", r.headers["X-RateLimit-Reset"])
        reset = int(r.headers["X-RateLimit-Reset"]) - time()
        if reset < 0:
            print("reset time            passed")
        else:
            print("reset time in         %.2f seconds" % reset)
        print("response code        ", r.status_code)
        if r.status_code in (503, 419):
            ic(r.headers)
        else:
            return r

print("\nLISTENBRAINZ")
for i in range(10):
    resp = http_get("https://api.listenbrainz.org/1/metadata/recording?recording_mbids=e97f805a-ab48-4c52-855e-07049142113d")
    print()

print("\nMUSICBRAINZ")
for i in range(10):
    resp = http_get("https://musicbrainz.org/ws/2/artist/8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11?fmt=json")
    print()
