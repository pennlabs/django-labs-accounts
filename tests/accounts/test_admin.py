from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LabsAdminTestCase(TestCase):
    def test_admin_not_logged_in(self):
        response = self.client.get(reverse("admin:login") + "?next=/admin/")
        redirect = "/accounts/login/?next=/admin/"
        self.assertRedirects(response, redirect, fetch_redirect_response=False)

    def test_admin_logged_in(self):
        get_user_model().objects.create_user(username="user", password="password", is_staff=True)
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("admin:login") + "?next=/admin/")
        redirect = "/admin/"
        self.assertRedirects(response, redirect, fetch_redirect_response=False)
