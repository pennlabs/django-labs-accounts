from unittest.mock import patch
import urllib.parse
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from labs_accounts.settings import CLIENT_ID, PLATFORM_URL, REDIRECT_URI, SCOPE


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_invalid_next(self):
        response = self.client.get(reverse('labs_accounts:login'))

    def test_authenticated_user(self):
        student = self.User.objects.create_user(
            username='00000000000000000000000000000001',
            uuid='00000000000000000000000000000001',
            password='secret'
        )
        self.client.login(username='00000000000000000000000000000001', password='secret')
        redirect = 'https://example.com/'
        response = self.client.get(reverse('labs_accounts:login') + '?next=' + redirect)
        self.assertRedirects(response, redirect, fetch_redirect_response=False)

    def test_unauthenticated_user(self):
        redirect = 'https://example.com/'
        response = self.client.get(reverse('labs_accounts:login') + '?next=' + redirect)
        self.assertEqual(response.status_code, 302)
        self.assertIn(PLATFORM_URL + '/accounts/authorize', response.url)
        self.assertIn('response_type=code', response.url)
        self.assertIn('client_id=' + CLIENT_ID, response.url)
        self.assertIn('redirect_uri=' + urllib.parse.quote_plus(REDIRECT_URI), response.url)
        self.assertIn('scope=' + '+'.join(SCOPE), response.url)


@patch('labs_accounts.views.OAuth2Session.get')
@patch('labs_accounts.views.OAuth2Session.fetch_token')
class CallbackViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = 'https://example.com/'
        session = self.client.session
        session['state'] = 'random_x'
        session['next'] = self.redirect
        session.save()
        self.User = get_user_model()

    def test_active_user(self, mock_fetch_token, mock_get):
        mock_fetch_token.return_value = {'access_token': 'abc'}
        mock_get.return_value.json.return_value = {'uuid': '00000000000000000000000000000001'}
        response = self.client.get(reverse('labs_accounts:callback'))
        self.assertRedirects(response, self.redirect, fetch_redirect_response=False)

    def test_inactive_user(self, mock_fetch_token, mock_get):
        student = self.User.objects.create_user(
            username='00000000000000000000000000000001',
            uuid='00000000000000000000000000000001',
            password='secret',
            is_active=False
        )
        mock_fetch_token.return_value = {'access_token': 'abc'}
        mock_get.return_value.json.return_value = {'uuid': '00000000000000000000000000000001'}
        response = self.client.get(reverse('labs_accounts:callback'))
        self.assertEqual(response.status_code, 500)
