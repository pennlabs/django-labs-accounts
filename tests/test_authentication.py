from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


# Tests modified from django-rest-framework
# https://github.com/encode/django-rest-framework/blob/71e6c30034a1dd35a39ca74f86c371713e762c79/tests/authentication/test_authentication.py#L270  # noqa
@patch("accounts.authentication.requests.post")
class PlatformAuthenticationTestCase(TestCase):
    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.path = "/token/"
        self.header_prefix = "Bearer "
        self.auth = f"{self.header_prefix}abc"

        self.user = User.objects.create(id=123, username="username")
        self.headers = {}
        self.valid_response = {  # Response from introspect
            "exp": 1123,
            "user": {
                "pennid": 123,
                "first_name": "first",
                "last_name": "last",
                "username": "abc",
                "email": "test@test.com",
                "affiliation": [],
                "user_permissions": [],
                "groups": ["student", "member"],
                "token": {
                    "access_token": "abc",
                    "refresh_token": "123",
                    "expires_in": 100,
                },
            },
        }

    def test_post_form_passing_token_auth(self, mock_request):
        """
        Ensure POSTing json over token auth with correct
        credentials passes and does not require CSRF
        """
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = self.valid_response

        response = self.csrf_client.post(
            self.path, {"example": "example"}, HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_post_form_passing_token_auth_new_user(self, mock_request):
        mock_request.return_value.status_code = 200
        self.valid_response["user"]["pennid"] = 456
        mock_request.return_value.json.return_value = self.valid_response

        response = self.csrf_client.post(
            self.path, {"example": "example"}, HTTP_AUTHORIZATION=self.auth
        )
        user = User.objects.get(id=456)
        self.assertEqual(user, response.wsgi_request.user)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_fail_authentication_if_user_is_not_active(self, mock_request):
        self.user.is_active = False
        self.user.save()
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = self.valid_response

        response = self.csrf_client.post(
            self.path, {"example": "example"}, HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_fail_post_form_passing_invalid_token_auth(self, mock_request):
        # platform response indicating access token is invalid
        mock_request.return_value.status_code = 403
        response = self.csrf_client.post(
            self.path, {"example": "example"}, HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_fail_post_if_token_is_missing(self, mock_request):
        response = self.csrf_client.post(
            self.path, {"example": "example"}, HTTP_AUTHORIZATION=self.header_prefix
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_fail_post_if_token_contains_spaces(self, mock_request):
        response = self.csrf_client.post(
            self.path,
            {"example": "example"},
            HTTP_AUTHORIZATION=self.header_prefix + "foo bar",
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_fail_post_if_connection_problem(self, mock_request):
        mock_request.side_effect = RequestException
        response = self.csrf_client.post(
            self.path,
            {"example": "example"},
            HTTP_AUTHORIZATION=self.header_prefix + "foobar",
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_post_json_passing_token_auth(self, mock_request):
        """
        Ensure POSTing form over token auth with correct
        credentials passes and does not require CSRF
        """
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = self.valid_response

        response = self.csrf_client.post(
            self.path,
            {"example": "example"},
            format="json",
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_post_form_failing_token_auth(self, mock_request):
        """
        Ensure POSTing form over token auth without correct credentials fails
        """
        response = self.csrf_client.post(self.path, {"example": "example"})
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_post_json_failing_token_auth(self, mock_request):
        """
        Ensure POSTing json over token auth without correct credentials fails
        """
        response = self.csrf_client.post(
            self.path, {"example": "example"}, format="json"
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
