from unittest.mock import patch

from django.test import TestCase

from identity.apps import IdentityConfig


class AppsTestCase(TestCase):
    def test_apps(self):
        self.assertEqual(IdentityConfig.name, "identity")

    @patch("identity.apps.attest")
    @patch("identity.apps.get_platform_jwks")
    def test_ready(self, mock_jwks, mock_attest):
        IdentityConfig.ready(None)
        mock_jwks.assert_called()
        mock_attest.assert_called()
