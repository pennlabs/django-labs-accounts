from unittest.mock import MagicMock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from identity.identity import container
from identity.permissions import B2BPermission
from tests.identity.utils import configure_container


class B2BTPermissionTestCase(TestCase):
    def test_invalid_urn(self):
        self.assertRaises(ImproperlyConfigured, B2BPermission, "fake:urn")

    def test_valid_urn(self):
        B2BPermission("urn:pennlabs:platform")


class B2BTPermissionInnerTestCase(TestCase):
    def setUp(self):
        configure_container(self)
        self.permission = B2BPermission("urn:pennlabs:*")()

    def test_invalid_access_jwt(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer abc"}
        request = MagicMock(META=headers)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_valid_access_jwt_all_urn(self):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {container.access_jwt.serialize()}"}
        request = MagicMock(META=headers)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_valid_access_jwt_right_urn(self):
        self.permission = B2BPermission("urn:pennlabs:example")()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {container.access_jwt.serialize()}"}
        request = MagicMock(META=headers)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_valid_access_jwt_wrong_urn(self):
        self.permission = B2BPermission("urn:fake:*")()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {container.access_jwt.serialize()}"}
        request = MagicMock(META=headers)
        self.assertFalse(self.permission.has_permission(request, None))

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
