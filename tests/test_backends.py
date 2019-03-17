from django.test import TestCase
from django.contrib import auth
from django.contrib.auth import get_user_model


class BackendTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_invalid_remote_user(self):
        user = auth.authenticate(remote_user=None)
        self.assertIsNone(user)

    def test_create_user(self):
        user = auth.authenticate(remote_user='00000000000000000000000000000001')
        self.assertEqual(len(self.User.objects.all()), 1)
        self.assertEqual(str(self.User.objects.all()[0].uuid), '00000000-0000-0000-0000-000000000001')
        self.assertEqual(str(self.User.objects.all()[0]), '00000000000000000000000000000001')

    def test_login_user(self):
        student = self.User.objects.create_user(
            username='00000000000000000000000000000001',
            uuid='00000000000000000000000000000001',
            password='secret'
        )
        user = auth.authenticate(remote_user='00000000000000000000000000000001')
        self.assertEqual(user, student)
