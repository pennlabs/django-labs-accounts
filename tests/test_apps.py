from django.test import TestCase

from accounts.apps import AccountsConfig


class AppsTestCase(TestCase):
    def test_apps(self):
        self.assertEqual(AccountsConfig.name, 'accounts')
