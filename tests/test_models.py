from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import AccessToken, RefreshToken


class AccessTokenTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username='abc')
        self.token = '123'
        self.accesstoken = AccessToken.objects.create(
            user=self.user,
            token=self.token,
            expires_at=timezone.now(),
        )

    def test_str(self):
        self.assertEqual(str(self.accesstoken), self.token)


class RefreshTokenTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username='abc')
        self.token = '123'
        self.refreshtoken = RefreshToken.objects.create(user=self.user, token=self.token)

    def test_str(self):
        self.assertEqual(str(self.refreshtoken), self.token)
