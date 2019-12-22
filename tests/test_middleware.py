from unittest.mock import Mock, patch

import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from accounts.middleware import OAuth2TokenMiddleware


@patch("accounts.middleware.requests.post")
class OAuth2TokenMiddlewareTestCase(TestCase):
    def setUp(self):
        self.request = Mock()
        self.request.META = {}
        self.request.user = AnonymousUser
        self.middleware = OAuth2TokenMiddleware(Mock())
        self.user = get_user_model().objects.create(id=123, username="username")
        self.valid_response = {"user": {"pennid": "123"}}

    def test_no_authorization_header(self, mock_request):
        self.middleware(self.request)
        self.assertEqual(AnonymousUser, self.request.user)

    def test_authorization_header_wrong_type(self, mock_request):
        self.request.META["HTTP_AUTHORIZATION"] = "Basic abc"
        self.middleware(self.request)
        self.assertEqual(AnonymousUser, self.request.user)

    def test_authorization_header_malformed(self, mock_request):
        self.request.META["HTTP_AUTHORIZATION"] = "Basic"
        self.middleware(self.request)
        self.assertEqual(AnonymousUser, self.request.user)

    def test_authorization_header_invalid(self, mock_request):
        mock_request.return_value.status_code = 403
        self.request.META["HTTP_AUTHORIZATION"] = "Bearer abc"
        self.middleware(self.request)
        self.assertEqual(AnonymousUser, self.request.user)

    def test_authorization_header_valid_user_exists(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = self.valid_response
        self.request.META["HTTP_AUTHORIZATION"] = "Bearer abc123"
        self.middleware(self.request)
        self.assertEqual(self.user, self.request.user)

    def test_authorization_header_valid_user_no_exists(self, mock_request):
        mock_request.return_value.status_code = 200
        self.valid_response["user"]["pennid"] = "456"
        mock_request.return_value.json.return_value = self.valid_response
        self.request.META["HTTP_AUTHORIZATION"] = "Bearer abc123"
        self.middleware(self.request)
        self.assertEqual(AnonymousUser, self.request.user)

    def test_authorization_header_valid_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.RequestException
        self.request.META["HTTP_AUTHORIZATION"] = "Bearer abc123"
        self.middleware(self.request)
        self.assertEqual(AnonymousUser, self.request.user)


@patch("accounts.middleware.requests.post")
class TestViewTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(id=123, username="username")
        self.headers = {}
        self.valid_response = {"user": {"pennid": "123"}}

    def test_no_authorization_header(self, mock_request):
        response = self.client.get(reverse("test"), **self.headers)
        self.assertEqual(200, response.status_code)

    def test_authorization_header_wrong_type(self, mock_request):
        self.headers["HTTP_AUTHORIZATION"] = "Basic abc"
        response = self.client.get(reverse("test"), **self.headers)
        self.assertEqual(200, response.status_code)

    def test_authorization_header_malformed(self, mock_request):
        self.headers["HTTP_AUTHORIZATION"] = "Basic"
        response = self.client.get(reverse("test"), **self.headers)
        self.assertEqual(200, response.status_code)

    def test_authorization_header_invalid(self, mock_request):
        mock_request.return_value.status_code = 403
        self.headers["HTTP_AUTHORIZATION"] = "Bearer abc"
        response = self.client.get(reverse("test"), **self.headers)
        self.assertEqual(403, response.status_code)

    def test_authorization_header_valid_user_exists(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = self.valid_response
        self.headers["HTTP_AUTHORIZATION"] = "Bearer abc123"
        response = self.client.get(reverse("test"), **self.headers)
        self.assertEqual(200, response.status_code)

    def test_authorization_header_valid_user_no_exists(self, mock_request):
        mock_request.return_value.status_code = 200
        self.valid_response["user"]["pennid"] = "456"
        mock_request.return_value.json.return_value = self.valid_response
        self.headers["HTTP_AUTHORIZATION"] = "Bearer abc123"
        response = self.client.get(reverse("test"), **self.headers)
        self.assertEqual(200, response.status_code)

    def test_authorization_header_valid_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.RequestException
        self.headers["HTTP_AUTHORIZATION"] = "Bearer abc123"
        response = self.client.get(reverse("test"), **self.headers)
        self.assertEqual(403, response.status_code)
