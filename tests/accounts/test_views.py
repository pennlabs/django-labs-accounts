import urllib.parse
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import AccessToken, RefreshToken
from accounts.settings import accounts_settings


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.redirect = "/abc"

    def test_invalid_next(self):
        response = self.client.get(
            reverse("accounts:login") + "?next=https://example.com"
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            accounts_settings.PLATFORM_URL + "/accounts/authorize/", response.url
        )

    def test_set_next(self):
        self.client.get(reverse("accounts:login") + "?next=/")
        self.assertIn("next", self.client.session)
        self.assertEqual("/", self.client.session["next"])
        self.assertIn("state", self.client.session)

    def test_authenticated_user(self):
        self.User.objects.create_user(username="user", password="secret")
        self.client.login(username="user", password="secret")
        response = self.client.get(reverse("accounts:login") + "?next=" + self.redirect)
        self.assertRedirects(response, self.redirect, fetch_redirect_response=False)

    def test_unauthenticated_user(self):
        response = self.client.get(reverse("accounts:login") + "?next=" + self.redirect)
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            accounts_settings.PLATFORM_URL + "/accounts/authorize", response.url
        )
        self.assertIn("response_type=code", response.url)
        self.assertIn("client_id=" + accounts_settings.CLIENT_ID, response.url)
        self.assertIn(
            "redirect_uri=" + urllib.parse.quote_plus(accounts_settings.REDIRECT_URI),
            response.url,
        )
        self.assertIn("scope=" + "+".join(accounts_settings.SCOPE), response.url)

    def test_autogenerated_redirect(self):
        accounts_settings.REDIRECT_URI = ""
        response = self.client.get(reverse("accounts:login") + "?next=" + self.redirect)
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            accounts_settings.PLATFORM_URL + "/accounts/authorize", response.url
        )
        self.assertIn("response_type=code", response.url)
        self.assertIn("client_id=" + accounts_settings.CLIENT_ID, response.url)
        self.assertIn(
            "redirect_uri=" + urllib.parse.quote_plus("http://testserver"), response.url
        )
        self.assertIn("scope=" + "+".join(accounts_settings.SCOPE), response.url)


@patch("accounts.views.OAuth2Session.post")
@patch("accounts.views.OAuth2Session.fetch_token")
class CallbackViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = "/abc"
        self.session = self.client.session
        self.session["state"] = "random_x"
        self.session["next"] = self.redirect
        self.session.save()
        self.User = get_user_model()
        self.mock_post = {  # Response from introspect
            "user": {
                "pennid": 1,
                "first_name": "First",
                "last_name": "Last",
                "username": "user",
                "email": "test@test.com",
                "affiliation": [],
                "user_permissions": [],
                "groups": ["student", "member"],
            }
        }

    def test_active_user(self, mock_fetch_token, mock_post):
        mock_fetch_token.return_value = {  # Response from token
            "access_token": "abc",
            "refresh_token": "123",
            "expires_in": 100,
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.mock_post
        response = self.client.get(reverse("accounts:callback"))
        self.assertRedirects(response, self.redirect, fetch_redirect_response=False)

    def test_inactive_user(self, mock_fetch_token, mock_post):
        self.User.objects.create_user(
            id=1, username="user", password="secret", is_active=False
        )
        mock_fetch_token.return_value = {
            "access_token": "abc",
            "refresh_token": "123",
            "expires_in": 100,
        }
        mock_post.return_value.json.return_value = self.mock_post
        response = self.client.get(reverse("accounts:callback"))
        self.assertEqual(response.status_code, 500)

    def test_missing_next(self, mock_fetch_token, mock_post):
        mock_fetch_token.return_value = {  # Response from token
            "access_token": "abc",
            "refresh_token": "123",
            "expires_in": 100,
        }
        del self.session["next"]
        self.session.save()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.mock_post
        response = self.client.get(reverse("accounts:callback"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_invalid_next(self, mock_fetch_token, mock_post):
        mock_fetch_token.return_value = {  # Response from token
            "access_token": "abc",
            "refresh_token": "123",
            "expires_in": 100,
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.mock_post
        self.session["next"] = "http://example.com"
        self.session.save()
        response = self.client.get(reverse("accounts:callback"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_logged_in_user(self):
        self.User.objects.create_user(username="user", password="secret")
        self.client.login(username="user", password="secret")
        response = self.client.get(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
        sample_response = "/"
        self.assertRedirects(response, sample_response, fetch_redirect_response=False)

    def test_guest_user(self):
        response = self.client.get(reverse("accounts:logout"))
        sample_response = "/"
        self.assertRedirects(response, sample_response, fetch_redirect_response=False)

    def test_redirect(self):
        response = self.client.get(reverse("accounts:logout") + "?next=/abc")
        sample_response = "/abc"
        self.assertRedirects(response, sample_response, fetch_redirect_response=False)

    def test_missing_next(self):
        response = self.client.get(reverse("accounts:logout"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_invalid_next(self):
        response = self.client.get(
            reverse("accounts:logout") + "?next=http://example.com"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")


class TokenViewTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.client = Client()
        self.mock_requests_json = {
            "access_token": "abc",
            "refresh_token": "123",
            "expires_in": 100,
            "token_type": "Bearer",
            "scope": "read introspection",
        }
        # Response from introspect
        self.mock_oauth_json = {
            "user": {
                "pennid": 1,
                "first_name": "First",
                "last_name": "Last",
                "username": "user",
                "email": "test@test.com",
                "affiliation": [],
                "user_permissions": [],
                "groups": ["student", "member"],
            }
        }

    @patch("accounts.views.OAuth2Session.post")
    @patch("accounts.views.requests.post")
    def test_token_valid(self, mock_requests_post, mock_oauth_post):
        mock_requests_post.return_value.json.return_value = self.mock_requests_json
        mock_requests_post.return_value.status_code = 200
        mock_oauth_post.return_value.json.return_value = self.mock_oauth_json
        mock_oauth_post.return_value.status_code = 200
        user = self.User.objects.create(id=1, username="user", password="secret")
        payload = {
            "grant_type": "correct_grant_type",
            "client_id": "correct_client_id",
            "refresh_token": "correct_refresh_token",
        }
        response = self.client.post(reverse("accounts:token"), payload)
        self.assertEqual(200, response.status_code)
        res_json = response.json()
        # Assert response is same as Platform response
        self.assertEqual(
            self.mock_requests_json["access_token"], res_json["access_token"]
        )
        self.assertEqual(
            self.mock_requests_json["refresh_token"], res_json["refresh_token"]
        )
        self.assertEqual(self.mock_requests_json["expires_in"], res_json["expires_in"])
        # Assert Access and Refresh tokens are correctly created in the backend
        self.assertEqual(len(AccessToken.objects.all()), 1)
        self.assertEqual(len(RefreshToken.objects.all()), 1)
        self.assertEqual(
            self.mock_requests_json["access_token"], user.accesstoken.token
        )
        self.assertEqual(
            self.mock_requests_json["refresh_token"], user.refreshtoken.token
        )

    @patch("accounts.views.OAuth2Session.post")
    @patch("accounts.views.requests.post")
    def test_token_unknown_user(self, mock_requests_post, mock_oauth_post):
        mock_requests_post.return_value.json.return_value = self.mock_requests_json
        mock_requests_post.return_value.status_code = 200
        mock_oauth_post.return_value.json.return_value = self.mock_oauth_json
        mock_oauth_post.return_value.status_code = 200
        payload = {
            "grant_type": "correct_grant_type",
            "client_id": "correct_client_id",
            "code": "correct_code",
            "redirect_uri": "https://example.com",
            "verifier": "correct_verifier",
        }
        response = self.client.post(reverse("accounts:token"), payload)
        # If no User object, token should still go through, however
        # no access and refresh tokens will be stored
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(AccessToken.objects.all()), 0)
        self.assertEqual(len(RefreshToken.objects.all()), 0)

    @patch("accounts.views.requests.post")
    def test_token_invalid_introspect(self, mock_requests_post):
        mock_requests_post.return_value.json.return_value = self.mock_requests_json
        mock_requests_post.return_value.status_code = 200
        payload = {
            "grant_type": "correct_grant_type",
            "client_id": "correct_client_id",
            "code": "correct_code",
            "redirect_uri": "https://example.com",
            "verifier": "correct_verifier",
        }
        response = self.client.post(reverse("accounts:token"), payload)
        # Should fail because introspect invalidated the provided access token
        self.assertEqual(403, response.status_code)

    def test_token_invalid_parameters(self):
        payload = {
            "grant_type": "invalid_grant_type",
            "client_id": "invalid_client_id",
            "refresh_token": "invalid_refresh",
        }
        response = self.client.post(reverse("accounts:token"), payload)
        # Should fail because Platform request should invalidate the payload
        self.assertEqual(400, response.status_code)
