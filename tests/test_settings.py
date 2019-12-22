from django.test import TestCase
from tests.settings import PLATFORM_ACCOUNTS

from accounts.settings import DEFAULTS, accounts_settings


class SettingsTestCase(TestCase):
    def test_invalid_setting(self):
        with self.assertRaises(AttributeError):
            accounts_settings.INVALID_SETTING

    def test_defined_setting(self):
        self.assertEqual(accounts_settings.CLIENT_ID, PLATFORM_ACCOUNTS["CLIENT_ID"])

    def test_default_setting(self):
        self.assertEqual(accounts_settings.SCOPE, DEFAULTS["SCOPE"])
