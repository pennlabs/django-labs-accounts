import urllib.parse
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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