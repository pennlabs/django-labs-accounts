from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class JWTViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_set_next(self):
        x = self.client.get(reverse("analytics:attest"))
        print(x.content)
        self.assertFalse(True)


class RefreshJWTViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_set_next(self):
        x = self.client.post(reverse("analytics:refresh"), {"refresh": ""})
        print(x.content)
        self.assertFalse(True)
