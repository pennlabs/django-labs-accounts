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
        self.student_group, _ = Group.objects.get_or_create(name="student")
        self.student_group.save()
        self.staff_group, _ = Group.objects.get_or_create(name="platform_staff")
        self.staff_group.save()
        self.test_user = self.User.objects.create(
            id=2, first_name="First", last_name="Last", username="test", email="email@test.com"
        )
        self.test_user.groups.add(self.student_group, self.staff_group)

    def test_invalid_remote_user(self):
        user = auth.authenticate(remote_user=None)
        self.assertIsNone(user)

    def test_create_user(self):
        self.assertEqual(len(self.User.objects.all()), 1)
        auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(len(self.User.objects.all()), 2)
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
        self.assertEqual(len(self.User.objects.all()), 1)
        auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(len(self.User.objects.all()), 2)
        self.remote_user["username"] = "changed_user"
        auth.authenticate(remote_user=self.remote_user)
        user = self.User.objects.all()[0]
        self.assertEqual(user.username, "changed_user")
        self.assertEqual(len(AccessToken.objects.all()), 1)
        self.assertEqual(len(RefreshToken.objects.all()), 1)
        self.assertEqual(self.remote_user["token"]["access_token"], user.accesstoken.token)
        self.assertEqual(self.remote_user["token"]["refresh_token"], user.refreshtoken.token)

    def test_login_user(self):
        self.assertEqual(len(self.User.objects.all()), 1)
        student = self.User.objects.create_user(id=1, username="user", password="secret")
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(user, student)
        self.assertEqual(len(self.User.objects.all()), 2)
        self.assertFalse(self.User.objects.all()[0].is_staff)

    def test_login_user_admin(self):
        self.remote_user["user_permissions"] = ["example_admin"]
        self.assertEqual(len(self.User.objects.all()), 1)
        student = self.User.objects.create_user(id=1, username="user", password="secret")
        user = auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(user, student)
        self.assertEqual(len(self.User.objects.all()), 2)
        self.assertTrue(self.User.objects.all()[0].is_staff)

    def test_create_user_admin(self):
        self.remote_user["user_permissions"] = ["example_admin"]
        self.assertEqual(len(self.User.objects.all()), 1)
        auth.authenticate(remote_user=self.remote_user)
        self.assertEqual(len(self.User.objects.all()), 2)
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
        self.assertEqual(2, user.groups.all().count())
        student = Group.objects.get(name="platform_student")
        member = Group.objects.get(name="platform_member")
        self.assertIn(student, user.groups.all())
        self.assertIn(member, user.groups.all())
        self.assertEqual(user.groups.all().count(), 2)

    def test_remove_group(self):
        user = auth.authenticate(
            remote_user={
                "pennid": self.test_user.id,
                "first_name": self.test_user.first_name,
                "last_name": self.test_user.last_name,
                "username": self.test_user.username,
                "email": self.test_user.email,
                "affiliation": [],
                "user_permissions": [],
                "groups": ["alum", "employee"],
                "token": {"access_token": "def", "refresh_token": "456", "expires_in": 100},
            }
        )
        self.assertEqual(3, user.groups.all().count())
        alum = Group.objects.get(name="platform_alum")
        employee = Group.objects.get(name="platform_employee")
        self.assertIn(alum, user.groups.all())
        self.assertIn(employee, user.groups.all())
        self.assertIn(self.student_group, user.groups.all())

    def test_custom_backend(self):
        with self.settings(AUTHENTICATION_BACKENDS=("tests.test_backends.CustomBackend",)):
            user = auth.authenticate(remote_user=self.remote_user)
            self.assertEqual(user.first_name, "Modified")


class CustomBackend(LabsUserBackend):
    def post_authenticate(self, user, created, dictionary):
        user.first_name = "Modified"
        user.save()
