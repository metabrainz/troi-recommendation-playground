import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import requests

import troi.http_request
from troi.http_request import MAX_RETRIES, http_fetch, http_get, http_post, retry_delay


class FakeHandler(BaseHTTPRequestHandler):

    def respond(self):
        self.server.requests.append(self.command)
        self.rfile.read(int(self.headers.get("Content-Length") or 0))

        status, headers = self.server.next_response()
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_GET = respond
    do_POST = respond

    def log_message(self, *args):
        pass


class FakeService(ThreadingHTTPServer):
    """ Replies with the queued responses, one per request, repeating the last one. """

    def __init__(self, responses):
        super().__init__(("127.0.0.1", 0), FakeHandler)
        self.responses = list(responses)
        self.requests = []
        self.lock = threading.Lock()

    def next_response(self):
        with self.lock:
            return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]

    @property
    def url(self):
        return "http://127.0.0.1:%d/" % self.server_address[1]


class TestHttpFetch(unittest.TestCase):
    """ These talk to a real socket rather than using requests_mock, which swaps out the
        transport adapter and so never exercises the urllib3 retry layer. """

    def setUp(self):
        backoff = patch.object(troi.http_request, "RETRY_BACKOFF", 0)
        backoff.start()
        self.addCleanup(backoff.stop)
        troi.http_request.domain_ratelimit_lookup.clear()

    def serve(self, *responses):
        service = FakeService(responses)
        threading.Thread(target=service.serve_forever, daemon=True).start()
        self.addCleanup(service.server_close)
        self.addCleanup(service.shutdown)
        return service

    def fetch(self, fn, url, **kwargs):
        """ Run the fetch on a thread so a hang fails the test instead of blocking it. """

        result = {}

        def run():
            try:
                result["response"] = fn(url, **kwargs)
            except Exception as err:
                result["error"] = err

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        thread.join(30)
        self.assertFalse(thread.is_alive(), "http_fetch never returned, it is looping forever")

        return result

    def test_post_gives_up_eventually(self):
        for status in (503, 429):
            with self.subTest(status=status):
                service = self.serve((status, {}))
                result = self.fetch(http_post, service.url, json={})

                self.assertNotIn("error", result)
                self.assertEqual(result["response"].status_code, status)
                self.assertEqual(len(service.requests), MAX_RETRIES + 1)

    def test_post_retries_a_transient_503(self):
        service = self.serve((503, {}), (503, {}), (200, {}))
        result = self.fetch(http_post, service.url, json={})

        self.assertEqual(result["response"].status_code, 200)
        self.assertEqual(len(service.requests), 3)

    def test_get_gives_up_eventually(self):
        """ GET is retried by urllib3 itself, which raises once the retries are spent. """

        service = self.serve((503, {}))
        result = self.fetch(http_get, service.url)

        self.assertIsInstance(result.get("error"), requests.exceptions.RetryError)

    def test_ratelimit_headers_are_kept(self):
        service = self.serve((200, {
            "X-RateLimit-Reset": "1700000000",
            "X-RateLimit-Remaining": "7",
            "X-RateLimit-Limit": "10"
        }))
        self.fetch(http_get, service.url)

        self.assertEqual(list(troi.http_request.domain_ratelimit_lookup.values()), [(10, 7, 1700000000)])

    def test_unparsable_ratelimit_headers_are_ignored(self):
        service = self.serve((200, {
            "X-RateLimit-Reset": "later",
            "X-RateLimit-Remaining": "7",
            "X-RateLimit-Limit": "10"
        }))
        result = self.fetch(http_get, service.url)

        self.assertNotIn("error", result)
        self.assertEqual(result["response"].status_code, 200)
        self.assertEqual(troi.http_request.domain_ratelimit_lookup, {})

    def test_only_get_and_post_are_supported(self):
        with self.assertRaises(ValueError):
            http_fetch("http://127.0.0.1/", "PUT")


class TestRetryDelay(unittest.TestCase):

    def delay(self, attempt, **headers):
        r = requests.Response()
        r.headers.update(headers)
        return retry_delay(r, attempt)

    def test_retry_after_wins(self):
        self.assertEqual(self.delay(0, **{"Retry-After": "12"}), 12.0)

    def test_negative_retry_after_is_clamped(self):
        self.assertEqual(self.delay(0, **{"Retry-After": "-5"}), 0.0)

    def test_retry_after_as_a_date_falls_back(self):
        backoff = troi.http_request.RETRY_BACKOFF
        self.assertEqual(self.delay(2, **{"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}), backoff * 4)

    def test_backoff_doubles(self):
        backoff = troi.http_request.RETRY_BACKOFF
        self.assertEqual([self.delay(i) for i in range(4)], [backoff * m for m in (1, 2, 4, 8)])


if __name__ == "__main__":
    unittest.main()
