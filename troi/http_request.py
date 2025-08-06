import requests
from time import time, sleep
from threading import Lock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse

# Index keep track of rate limits of the various services 
# we may call. key: scheme, domain value: RateLimit-Limit, Remaining, Reset
ratelimit_lock = Lock()
domain_ratelimit_lookup = {}

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504, 503, 429),
    session=None,
):
    """ Create the session object for retry handling """

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
    """ Convenience function for http get"""
    return http_fetch(url, "GET", headers=headers, params=params, **kwargs)

def http_post(url, headers=None, params=None, **kwargs):
    """ Convenience function for http post"""
    return http_fetch(url, "POST", headers=headers, params=params, **kwargs)

def http_put(url, headers=None, params=None, **kwargs):
    """ Convenience function for http put"""
    return http_fetch(url, "PUT", headers=headers, params=params, **kwargs)

def http_fetch(url, method, headers=None, params=None, **kwargs):
    """ HTTP fetch wrapper that uses HTTPAdapter sessions with back-off retries
        and support for delaying calls based on the RateLimit headers provided
        by the API. Note: MusicBrainz' Rate Limit headers are busted, so we use a 1s
        delay for that. Will need to remove after https://tickets.metabrainz.org/browse/MBH-589
        is fixed. """

    global ratelimit_lock

    if not headers:
        headers = {}
    headers["User-Agent"] = "ListenBrainz Troi (rob@meb)"

    if method not in ("GET", "POST"):
        raise ValueError("Only GET and POST are supported.")

    session = requests_retry_session()
    parse = urlparse(url)
    while True:
        _key = parse.scheme + parse.netloc
        ratelimit_lock.acquire()
        have_key = _key in domain_ratelimit_lookup
        ratelimit_lock.release()
        if have_key:
            ratelimit_lock.acquire()
            (limit, remaining, reset) = domain_ratelimit_lookup[_key]
            ratelimit_lock.release()

            # MB's rate limit headers are borked, so for the time being, use nearly 1s
            if parse.netloc.startswith("musicbrainz.org"):
                time_left = .9
            else:
                time_left = reset - time()
                if time_left > 0:
                    time_to_wait = time_left / remaining
                    sleep(time_to_wait)

            ratelimit_lock.acquire()
            del domain_ratelimit_lookup[_key]
            ratelimit_lock.release()

        if method == "GET":
            r = session.get(url, params=params, headers=headers, **kwargs)
        else:
            r = session.post(url, params=params, headers=headers, **kwargs)

        try:
            reset = int(r.headers["X-RateLimit-Reset"])
            remaining = int(r.headers["X-RateLimit-Remaining"])
            limit = int(r.headers["X-RateLimit-Limit"])
            ratelimit_lock.acquire()
            domain_ratelimit_lookup[_key] = (limit, remaining, reset)
            ratelimit_lock.release()
        except KeyError:
            pass

        # This should never happen, but if it does, just retry
        if r.status_code in (503, 429):
            continue

        return r
