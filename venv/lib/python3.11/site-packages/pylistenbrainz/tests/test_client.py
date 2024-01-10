# pylistenbrainz - A simple client library for ListenBrainz
# Copyright (C) 2020 Param Singh <iliekcomputers@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import pylistenbrainz
import requests
import time
import unittest
import uuid

from pylistenbrainz import errors
from unittest import mock

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testdata')


class ListenBrainzClientTestCase(unittest.TestCase):

    def setUp(self):
        self.client = pylistenbrainz.ListenBrainz()

    @mock.patch('pylistenbrainz.client.requests.get')
    def test_get_injects_auth_token_if_available(self, mock_requests_get):
        mock_requests_get.return_value = mock.MagicMock()
        self.client._get('/1/user/iliekcomputers/listens')
        mock_requests_get.assert_called_once_with(
            'https://api.listenbrainz.org/1/user/iliekcomputers/listens',
            params={},
            headers={},
        )

        mock_requests_get.reset_mock()
        self.client.is_token_valid = mock.MagicMock(return_value=True)
        auth_token = str(uuid.uuid4())
        self.client.set_auth_token(auth_token)
        self.client._get('/1/user/iliekcomputers/listens')
        mock_requests_get.assert_called_once_with(
            'https://api.listenbrainz.org/1/user/iliekcomputers/listens',
            params={},
            headers={'Authorization': f'Token {auth_token}'}
        )


    @mock.patch('pylistenbrainz.client.requests.post')
    def test_post_injects_auth_token_if_available(self, mock_requests_post):
        mock_requests_post.return_value = mock.MagicMock()
        self.client._post('/1/user/iliekcomputers/listens')
        mock_requests_post.assert_called_once_with(
            'https://api.listenbrainz.org/1/user/iliekcomputers/listens',
            data=None,
            headers={},
        )

        mock_requests_post.reset_mock()
        self.client.is_token_valid = mock.MagicMock(return_value=True)
        auth_token = str(uuid.uuid4())
        self.client.set_auth_token(auth_token)
        self.client._post('/1/user/iliekcomputers/listens')
        mock_requests_post.assert_called_once_with(
            'https://api.listenbrainz.org/1/user/iliekcomputers/listens',
            data=None,
            headers={'Authorization': f'Token {auth_token}'}
        )


    def test_client_get_listens(self):
        self.client._get = mock.MagicMock()
        with open(os.path.join(TEST_DATA_DIR, 'get_listens_happy_path_response.json')) as f:
            response_json = json.load(f)
        self.client._get.return_value = response_json
        received_listens = self.client.get_listens('iliekcomputers')
        expected_listens = response_json['payload']['listens']
        self.client._get.assert_called_once_with(
            '/1/user/iliekcomputers/listens',
            params={},
        )
        for i in range(len(expected_listens)):
            self.assertEqual(received_listens[i].listened_at, expected_listens[i]['listened_at'])
            self.assertEqual(received_listens[i].track_name, expected_listens[i]['track_metadata']['track_name'])


    def test_client_get_listens_with_max_ts(self):
        ts = int(time.time())
        self.client._get = mock.MagicMock()
        with open(os.path.join(TEST_DATA_DIR, 'get_listens_happy_path_response.json')) as f:
            response_json = json.load(f)
        self.client._get.return_value = response_json
        received_listens = self.client.get_listens('iliekcomputers', max_ts=ts)
        self.client._get.assert_called_once_with(
            '/1/user/iliekcomputers/listens',
            params={'max_ts': ts},
        )
        expected_listens = response_json['payload']['listens']
        for i in range(len(expected_listens)):
            self.assertEqual(received_listens[i].listened_at, expected_listens[i]['listened_at'])
            self.assertEqual(received_listens[i].track_name, expected_listens[i]['track_metadata']['track_name'])


    def test_client_get_listens_with_min_ts(self):
        ts = int(time.time())
        self.client._get = mock.MagicMock()
        with open(os.path.join(TEST_DATA_DIR, 'get_listens_happy_path_response.json')) as f:
            response_json = json.load(f)
        self.client._get.return_value = response_json
        received_listens = self.client.get_listens('iliekcomputers', min_ts=ts)
        self.client._get.assert_called_once_with(
            '/1/user/iliekcomputers/listens',
            params={'min_ts': ts},
        )
        expected_listens = response_json['payload']['listens']
        for i in range(len(expected_listens)):
            self.assertEqual(received_listens[i].listened_at, expected_listens[i]['listened_at'])
            self.assertEqual(received_listens[i].track_name, expected_listens[i]['track_metadata']['track_name'])


    def test_client_get_listens_with_count(self):
        self.client._get = mock.MagicMock()
        with open(os.path.join(TEST_DATA_DIR, 'get_listens_happy_path_response.json')) as f:
            response_json = json.load(f)
        self.client._get.return_value = response_json
        received_listens = self.client.get_listens('iliekcomputers', count=50)
        self.client._get.assert_called_once_with(
            '/1/user/iliekcomputers/listens',
            params={'count': 50},
        )
        expected_listens = response_json['payload']['listens']
        for i in range(len(expected_listens)):
            self.assertEqual(received_listens[i].listened_at, expected_listens[i]['listened_at'])
            self.assertEqual(received_listens[i].track_name, expected_listens[i]['track_metadata']['track_name'])


    def test_client_get_playing_now(self):
        self.client._get = mock.MagicMock()
        with open(os.path.join(TEST_DATA_DIR, 'get_playing_now_happy_path_response.json')) as f:
            response_json = json.load(f)
        self.client._get.return_value = response_json
        received_listen = self.client.get_playing_now('iliekcomputers')
        self.client._get.assert_called_once_with(
            '/1/user/iliekcomputers/playing-now',
        )
        expected_listen = response_json['payload']['listens'][0]
        self.assertIsNotNone(received_listen)
        self.assertIsNone(received_listen.listened_at)
        self.assertEqual(received_listen.track_name, expected_listen['track_metadata']['track_name'])


    def test_client_get_playing_now_no_listen(self):
        self.client._get = mock.MagicMock()
        with open(os.path.join(TEST_DATA_DIR, 'no_playing_now.json')) as f:
            response_json = json.load(f)
        self.client._get.return_value = response_json
        received_listen = self.client.get_playing_now('iliekcomputers')
        self.client._get.assert_called_once_with(
            '/1/user/iliekcomputers/playing-now',
        )
        self.assertIsNone(received_listen)

    @mock.patch('pylistenbrainz.client.requests.post')
    @mock.patch('pylistenbrainz.client.json.dumps')
    def test_submit_single_listen(self, mock_json_dumps, mock_requests_post):
        ts = int(time.time())
        listen = pylistenbrainz.Listen(
            track_name="Fade",
            artist_name="Kanye West",
            release_name="The Life of Pablo",
            listened_at=ts,
        )

        expected_payload = {
            'listen_type': 'single',
            'payload': [
                {
                    'listened_at': ts,
                    'track_metadata': {
                        'track_name': 'Fade',
                        'artist_name': 'Kanye West',
                        'release_name': 'The Life of Pablo',
                    }
                }
            ]
        }

        mock_json_dumps.return_value = "mock data to be sent"
        mock_requests_post.return_value.json.return_value = {'status': 'ok'}
        auth_token = str(uuid.uuid4())
        self.client.is_token_valid = mock.MagicMock(return_value=True)
        self.client.set_auth_token(auth_token)
        response = self.client.submit_single_listen(listen)
        mock_requests_post.assert_called_once_with(
            'https://api.listenbrainz.org/1/submit-listens',
            data="mock data to be sent",
            headers={'Authorization': f'Token {auth_token}'}
        )
        mock_json_dumps.assert_called_once_with(expected_payload)
        self.assertEqual(response['status'], 'ok')

    def test_submit_payload_exceptions(self):
        ts = int(time.time())
        listen = pylistenbrainz.Listen(
            track_name="Fade",
            artist_name="Kanye West",
            release_name="The Life of Pablo",
            listened_at=ts,
        )

        # check that it doesn't try to submit without an auth token
        with self.assertRaises(errors.AuthTokenRequiredException):
            self.client.submit_multiple_listens([listen])

        # now, we set an auth token
        auth_token = str(uuid.uuid4())
        self.client.is_token_valid = mock.MagicMock(return_value=True)
        self.client.set_auth_token(auth_token)

        # check that we don't allow submission of zero listens
        with self.assertRaises(errors.EmptyPayloadException):
            self.client.submit_multiple_listens([])

        # test that we check for validity of listen types
        with self.assertRaises(errors.UnknownListenTypeException):
            self.client._post_submit_listens([listen], 'unknown listen type')

        # test that we don't allow submission of multiple listens
        # with the "single" or "playing now" types
        with self.assertRaises(errors.TooManyListensException):
            self.client._post_submit_listens([listen, listen], 'single')

        with self.assertRaises(errors.TooManyListensException):
            self.client._post_submit_listens([listen, listen], 'playing_now')

        # test that we don't submit timestamps for playingnow listens
        with self.assertRaises(errors.ListenedAtInPlayingNowException):
            self.client.submit_playing_now(listen)

    def test_set_auth_token_invalid_token(self):
        self.client.is_token_valid = mock.MagicMock(return_value=False)

        with self.assertRaises(errors.InvalidAuthTokenException):
            self.client.set_auth_token(str(uuid.uuid4()))

    def test_set_auth_token_valid_token(self):
        self.client.is_token_valid = mock.MagicMock(return_value=True)
        auth_token = str(uuid.uuid4())
        self.client.set_auth_token(auth_token)
        self.assertEqual(auth_token, self.client._auth_token)

    @mock.patch('pylistenbrainz.client.requests.post')
    def test_post_api_exceptions(self, mock_requests_post):
        response = mock.MagicMock()
        response.json.return_value = {'code': 401, 'error': 'Unauthorized'}
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        mock_requests_post.return_value = response

        # set auth token
        self.client.is_token_valid = mock.MagicMock(return_value=True)
        auth_token = str(uuid.uuid4())
        self.client.set_auth_token(auth_token)

        # create a listen
        ts = int(time.time())
        listen = pylistenbrainz.Listen(
            track_name="Fade",
            artist_name="Kanye West",
            release_name="The Life of Pablo",
            listened_at=ts,
        )

        # assert that submitting it raises a ListenBrainzAPIException
        with self.assertRaises(errors.ListenBrainzAPIException):
            self.client.submit_single_listen(listen)

    @mock.patch('pylistenbrainz.client.requests.get')
    def test_get_api_exceptions(self, mock_requests_get):
        response = mock.MagicMock()
        response.json.return_value = {'code': 401, 'error': 'Unauthorized'}
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        mock_requests_get.return_value = response

        # assert that getting listens raises a ListenBrainzAPIException
        with self.assertRaises(errors.ListenBrainzAPIException):
            self.client.get_listens('iliekcomputers')


    @mock.patch('pylistenbrainz.client.requests.get')
    def test_get_user_recommendation_recordings(self, mock_requests_get):
        mock_requests_get.return_value = mock.MagicMock()
        with self.assertRaises(ValueError):
            self.client.get_user_recommendation_recordings("boo", "bad artist type")

        mock_requests_get.reset_mock()
        mock_requests_get.return_value = mock.MagicMock()
        self.client.get_user_recommendation_recordings("iliekcomputers", "top", offset=3, count=2)
        mock_requests_get.assert_called_once_with(
            'https://api.listenbrainz.org/1/cf/recommendation/user/iliekcomputers/recording',
            params={
                    'artist_type': 'top',
                    'count': 2,
                    'offset': 3
                   },
            headers={},
        )

        mock_requests_get.reset_mock()
        mock_requests_get.return_value = mock.MagicMock()
        self.client.get_user_recommendation_recordings("iliekcomputers", "similar", offset=3, count=2)
        mock_requests_get.assert_called_once_with(
            'https://api.listenbrainz.org/1/cf/recommendation/user/iliekcomputers/recording',
            params={
                    'artist_type': 'similar',
                    'count': 2,
                    'offset': 3
                   },
            headers={},
        )

    def test_get_user_listen_count(self):
        self.client._get = mock.MagicMock()

        test_response = {"payload":{"count":111487}}
        self.client._get.return_value = test_response
        returned_count = self.client.get_user_listen_count('iliekcomputers')
        self.client._get.assert_called_once_with('/1/user/iliekcomputers/listen-count')
        
        self.assertEqual(returned_count, test_response['payload']['count'])

