from datetime import timedelta
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from accounts.ipc import _refresh_access_token, authenticated_request
from accounts.models import AccessToken, RefreshToken


class AuthenticatedRequestTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username='abc')
        self.now = timezone.now()
        self.token = 'abc'
        AccessToken.objects.create(user=self.user, expires_at=self.now, token=self.token)
        RefreshToken.objects.create(user=self.user)

    @patch('accounts.ipc._refresh_access_token')
    def test_update_refresh_token_fail(self, mock_refresh):
        mock_refresh.return_value = False
        self.assertFalse(authenticated_request(self.user, None, None))

    @patch('accounts.ipc.requests.Session')
    def test_authorization_header(self, mock_session):
        header = {'abc': '123'}
        authenticated_request(self.user, None, None, headers=header)
        header['Authorization'] = f'Bearer {self.token}'
        arguments = mock_session.return_value.request.call_args[1]
        self.assertEqual(header, arguments['headers'])


@patch('accounts.ipc.requests.post')
class RefreshAccessTokenTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create(username='abc')
        self.now = timezone.now()
        AccessToken.objects.create(user=self.user, expires_at=self.now)
        RefreshToken.objects.create(user=self.user)
        self.valid_response = {
            'access_token': 'abc',
            'refresh_token': '123',
            'expires_in': 100
        }

    def test_valid_refresh_token(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.valid_response
        value = _refresh_access_token(self.user)
        diff = self.now + timedelta(seconds=self.valid_response['expires_in'])
        self.assertTrue(value)
        self.assertTrue(diff < self.user.accesstoken.expires_at)
        self.assertEqual(self.valid_response['access_token'], self.user.accesstoken.token)
        self.assertEqual(self.valid_response['refresh_token'], self.user.refreshtoken.token)

    def test_exception_occurred(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException
        value = _refresh_access_token(self.user)
        self.assertFalse(value)
        self.assertNotEqual(self.valid_response['access_token'], self.user.accesstoken.token)
        self.assertNotEqual(self.valid_response['refresh_token'], self.user.refreshtoken.token)
