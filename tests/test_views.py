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

    def test_invalid_next(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 400)

    def test_authenticated_user(self):
        self.User.objects.create_user(
            username='user',
            password='secret'
        )
        self.client.login(username='user', password='secret')
        redirect = 'https://example.com/'
        response = self.client.get(reverse('accounts:login') + '?next=' + redirect)
        self.assertRedirects(response, redirect, fetch_redirect_response=False)

    def test_unauthenticated_user(self):
        redirect = 'https://example.com/'
        response = self.client.get(reverse('accounts:login') + '?next=' + redirect)
        self.assertEqual(response.status_code, 302)
        self.assertIn(accounts_settings.PLATFORM_URL + '/accounts/authorize', response.url)
        self.assertIn('response_type=code', response.url)
        self.assertIn('client_id=' + accounts_settings.CLIENT_ID, response.url)
        self.assertIn('redirect_uri=' + urllib.parse.quote_plus(accounts_settings.REDIRECT_URI), response.url)
        self.assertIn('scope=' + '+'.join(accounts_settings.SCOPE), response.url)


@patch('accounts.views.OAuth2Session.post')
@patch('accounts.views.OAuth2Session.fetch_token')
class CallbackViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = 'https://example.com/'
        session = self.client.session
        session['state'] = 'random_x'
        session['next'] = self.redirect
        session.save()
        self.User = get_user_model()
        self.mock_post = {
            'user': {
                'pennid': '1',
                'first_name': 'First',
                'last_name': 'Last',
                'username': 'user',
                'email': 'test@test.com',
                'affiliation': [],
                'product_permission': []
            }
        }

    def test_active_user(self, mock_fetch_token, mock_post):
        mock_fetch_token.return_value = {'access_token': 'abc'}
        mock_post.return_value.json.return_value = self.mock_post
        response = self.client.get(reverse('accounts:callback'))
        self.assertRedirects(response, self.redirect, fetch_redirect_response=False)

    def test_inactive_user(self, mock_fetch_token, mock_post):
        self.User.objects.create_user(
            id=1,
            username='user',
            password='secret',
            is_active=False
        )
        mock_fetch_token.return_value = {'access_token': 'abc'}
        mock_post.return_value.json.return_value = self.mock_post
        response = self.client.get(reverse('accounts:callback'))
        self.assertEqual(response.status_code, 500)


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_logged_in_user(self):
        self.User.objects.create_user(username='user', password='secret')
        self.client.login(username='user', password='secret')
        response = self.client.get(reverse('accounts:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
        sample_response = '/'
        self.assertRedirects(response, sample_response, fetch_redirect_response=False)

    def test_guest_user(self):
        response = self.client.get(reverse('accounts:logout'))
        sample_response = '/'
        self.assertRedirects(response, sample_response, fetch_redirect_response=False)

    def test_redirect(self):
        response = self.client.get(reverse('accounts:logout') + '?next=http://example.com')
        sample_response = 'http://example.com'
        self.assertRedirects(response, sample_response, fetch_redirect_response=False)
