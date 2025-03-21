import requests
from time import time, sleep
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib.parse import urlparse

# Index keep track of rate limits of the various services 
# we may call. key: scheme, domain value: RateLimit-Limit, Remaining, Reset
domain_ratelimit_lookup = {}

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
    return http_fetch(url, "GET", headers=headers, params=params, **kwargs)

def http_post(url, headers=None, params=None, **kwargs):
    return http_fetch(url, "POST", headers=headers, params=params, **kwargs)

def http_fetch(url, method, headers=None, params=None, **kwargs):

    if not headers:
        headers = {}
    headers["User-Agent"] = "ListenBrainz Troi (rob@meb)"

    if method not in ("GET", "POST"):
        raise ValueError("Only GET and POST are supported.")

    session = requests_retry_session()
    parse = urlparse(url)
    while True:
        _key = parse.scheme + parse.netloc
        if _key in domain_ratelimit_lookup:
            (limit, remaining, reset) = domain_ratelimit_lookup[_key]
            time_left = reset - time()
            if time_left > 0:
                time_to_wait = time_left / remaining
                sleep(time_to_wait)
            del domain_ratelimit_lookup[_key]

        if method == "GET":
            r = session.get(url, params=params, headers=headers, **kwargs)
        else:
            r = session.post(url, params=params, headers=headers, **kwargs)

        reset = int(r.headers["X-RateLimit-Reset"])
        remaining = int(r.headers["X-RateLimit-Remaining"])
        limit = int(r.headers["X-RateLimit-Limit"])
        domain_ratelimit_lookup[_key] = (limit, remaining, reset)

        # This should never happen, but if it does, just retry
        if r.status_code in (503, 419):
            continue

        return r

if __name__ == "__main__":
    print("\nLISTENBRAINZ")
    for i in range(500):
        resp = http_get("https://api.listenbrainz.org/1/metadata/recording?recording_mbids=e97f805a-ab48-4c52-855e-07049142113d")

    #print("\nMUSICBRAINZ")
    #for i in range(10):
    #    resp = http_get("https://musicbrainz.org/ws/2/artist/8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11?fmt=json")
