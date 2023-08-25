from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.ipc import authenticated_request
from accounts.models import AccessToken, RefreshToken


class AuthenticatedRequestTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username="abc")
        self.now = timezone.now()
        self.token = "abc"
        AccessToken.objects.create(
            user=self.user, expires_at=self.now, token=self.token
        )
        RefreshToken.objects.create(user=self.user)

    @patch("accounts.ipc.requests.Session")
    def test_authorization_header(self, mock_session):
        header = {"abc": "123"}
        authenticated_request(self.user, None, None, headers=header)
        header["Authorization"] = f"Bearer {self.token}"
        arguments = mock_session.return_value.request.call_args[1]
        self.assertEqual(header, arguments["headers"])
