from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.backends import LabsUserBackend
from accounts.models import AccessToken, RefreshToken


class BackendTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.remote_user = {
            "pennid": 1,
            "first_name": "First",
            "last_name": "Last",
            "username": "user",
            "email": "test@test.com",
            "affiliation": [],
            "user_permissions": [],
            "groups": ["student", "member"],
            "token": {"access_token": "abc", "refresh_token": "123", "expires_in": 100},
        }

    def test_invalid_remote_user(self):
        user = auth.authenticate(remote_user=None)
        self.assertIsNone(user)

    def test_create_user(self):
        auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(len(self.User.objects.all()), 1)
        user = self.User.objects.all()[0]
        self.assertEqual(user.username, "user")
        self.assertEqual(user.first_name, "First")
        self.assertEqual(user.last_name, "Last")
        self.assertEqual(user.email, "test@test.com")
        self.assertFalse(self.User.objects.all()[0].is_staff)
        self.assertEqual(len(AccessToken.objects.all()), 1)
        self.assertEqual(len(RefreshToken.objects.all()), 1)
        self.assertEqual(self.remote_user["token"]["access_token"], user.accesstoken.token)
        self.assertEqual(self.remote_user["token"]["refresh_token"], user.refreshtoken.token)

    def test_update_user(self):
        auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(len(self.User.objects.all()), 1)
        self.remote_user["username"] = "changed_user"
        auth.authenticate(remote_user=self.remote_user)
        user = self.User.objects.all()[0]
        self.assertEqual(user.username, "changed_user")
        self.assertEqual(len(AccessToken.objects.all()), 1)
        self.assertEqual(len(RefreshToken.objects.all()), 1)
        self.assertEqual(self.remote_user["token"]["access_token"], user.accesstoken.token)
        self.assertEqual(self.remote_user["token"]["refresh_token"], user.refreshtoken.token)

    def test_login_user(self):
        student = self.User.objects.create_user(id=1, username="user", password="secret")
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(user, student)
        self.assertEqual(len(self.User.objects.all()), 1)
        self.assertFalse(self.User.objects.all()[0].is_staff)

    def test_login_user_admin(self):
        self.remote_user["user_permissions"] = ["example_admin"]
        student = self.User.objects.create_user(id=1, username="user", password="secret")
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(user, student)
        self.assertEqual(len(self.User.objects.all()), 1)
        self.assertTrue(self.User.objects.all()[0].is_staff)

    def test_create_user_admin(self):
        self.remote_user["user_permissions"] = ["example_admin"]
        auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(len(self.User.objects.all()), 1)
        self.assertEqual(self.User.objects.all()[0].username, "user")
        self.assertTrue(self.User.objects.all()[0].is_staff)

    def test_give_admin_permission(self):
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.remote_user["user_permissions"] = ["example_admin"]
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_remove_admin_permission(self):
        self.remote_user["user_permissions"] = ["example_admin"]
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.remote_user["user_permissions"] = []
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_add_group(self):
        self.remote_user["groups"] = []
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(0, user.groups.all().count())
        self.remote_user["groups"] = ["member", "student"]
        user = auth.authenticate(remote_user=self.remote_user)
        student = Group.objects.get(name="student")
        member = Group.objects.get(name="member")
        self.assertEqual(2, user.groups.all().count())
        self.assertIn(student, user.groups.all())
        self.assertIn(member, user.groups.all())

    def test_custom_backend(self):
        with self.settings(AUTHENTICATION_BACKENDS=("tests.test_backends.CustomBackend",)):
            user = auth.authenticate(remote_user=self.remote_user)
            self.assertEqual(user.first_name, "Modified")


class CustomBackend(LabsUserBackend):
    def post_authenticate(self, user, created, dictionary):
        user.first_name = "Modified"
        user.save()
