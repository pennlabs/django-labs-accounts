from unittest.mock import MagicMock

from django.test import TestCase

from identity.identity import container
from identity.permissions import B2BPermission
from tests.identity.utils import configure_container


class AppsTestCase(TestCase):
    def setUp(self):
        configure_container(self)
        self.permission = B2BPermission()

    def test_invalid_access_jwt(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer abc"}
        request = MagicMock(META=headers)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_valid_access_jwt(self):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {container.access_jwt.serialize()}"}
        request = MagicMock(META=headers)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_refresh_jwt(self):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {container.refresh_jwt.serialize()}"}
        request = MagicMock(META=headers)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_not_bearer(self):
        headers = {"HTTP_AUTHORIZATION": f"Token {container.access_jwt.serialize()}"}
        request = MagicMock(META=headers)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_no_headers(self):
        request = MagicMock(META={})
        self.assertFalse(self.permission.has_permission(request, None))
