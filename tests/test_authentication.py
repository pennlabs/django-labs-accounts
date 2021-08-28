from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# from accounts.middleware import OAuth2TokenMiddleware


# @patch("accounts.middleware.requests.post")
# class OAuth2TokenMiddlewareTestCase(TestCase):
#     def setUp(self):
#         self.request = Mock()
#         self.request.META = {}
#         self.request.user = AnonymousUser
#         self.middleware = OAuth2TokenMiddleware(Mock())
#         self.user = get_user_model().objects.create(id=123, username="username")
#         self.valid_response = {  # Response from introspect
#             "exp": 1123,
#             "user": {
#                 "pennid": 123,
#                 "first_name": "first",
#                 "last_name": "last",
#                 "username": "abc",
#                 "email": "test@test.com",
#                 "affiliation": [],
#                 "user_permissions": [],
#                 "groups": ["student", "member"],
#                 "token": {
#                     "access_token": "abc",
#                     "refresh_token": "123",
#                     "expires_in": 100,
#                 },
#             },
#         }

#     def test_authorization_header_valid_user_no_exists(self, mock_request):
#         mock_request.return_value.status_code = 200
#         self.valid_response["user"]["pennid"] = 456
#         mock_request.return_value.json.return_value = self.valid_response
#         self.request.META["HTTP_AUTHORIZATION"] = "Bearer abc123"
#         self.middleware(self.request)
#         user = get_user_model().objects.get(id=self.valid_response["user"]["pennid"])
#         self.assertEqual(user, self.request.user)

#     def test_authorization_header_valid_connection_error(self, mock_request):
#         mock_request.side_effect = requests.exceptions.RequestException
#         self.request.META["HTTP_AUTHORIZATION"] = "Bearer abc123"
#         self.middleware(self.request)
#         self.assertEqual(AnonymousUser, self.request.user)


#     def test_authorization_header_valid_user_no_exists(self, mock_request):
#         mock_request.return_value.status_code = 200
#         self.valid_response["user"]["pennid"] = "456"
#         mock_request.return_value.json.return_value = self.valid_response
#         self.headers["HTTP_AUTHORIZATION"] = "Bearer abc123"
#         response = self.client.get(reverse("test"), **self.headers)
#         self.assertEqual(200, response.status_code)

#     @patch("accounts.middleware.auth.authenticate")
#     def test_authorization_header_valid_server_error(
#         self, mock_authenticate, mock_request
#     ):
#         mock_authenticate.return_value = None
#         mock_request.return_value.status_code = 200
#         mock_request.return_value.json.return_value = self.valid_response
#         self.headers["HTTP_AUTHORIZATION"] = "Bearer abc123"
#         response = self.client.get(reverse("test"), **self.headers)
#         self.assertEqual(500, response.status_code)


# Tests modified from django-rest-framework
# https://github.com/encode/django-rest-framework/blob/71e6c30034a1dd35a39ca74f86c371713e762c79/tests/authentication/test_authentication.py#L270  # noqa
@patch("accounts.authentication.requests.post")
class PlatformAuthenticationTestCase(TestCase):
    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.path = "/token/"
        self.header_prefix = "Bearer "
        self.auth = f"{self.header_prefix}abc"

        self.user = get_user_model().objects.create(id=123, username="username")
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
        """
        Ensure POSTing json over token auth with correct
        credentials passes and does not require CSRF
        """
        mock_request.return_value.status_code = 200
        self.valid_response["user"]["pennid"] = 456
        mock_request.return_value.json.return_value = self.valid_response

        response = self.csrf_client.post(
            self.path, {"example": "example"}, HTTP_AUTHORIZATION=self.auth
        )
        # print(response.__dict__)
        # self.assertFalse(True)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    # def test_fail_authentication_if_user_is_not_active(self, mock_request):
    #     self.user.is_active = False
    #     self.user.save()
    #     mock_request.return_value.status_code = 200
    #     mock_request.return_value.json.return_value = self.valid_response

    #     response = self.csrf_client.post(
    #         self.path, {"example": "example"}, HTTP_AUTHORIZATION=self.auth
    #     )
    #     self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

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
