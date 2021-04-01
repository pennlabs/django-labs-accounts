import json
import time
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from identity.identity import (
    REFRESH_URL,
    _refresh_if_outdated,
    attest,
    authenticated_b2b_request,
    container,
    get_platform_jwks,
    validate_urn,
)
from tests.identity.utils import (
    ID_PRIVATE_KEY,
    PLATFORM_JWKS,
    configure_container,
    mint_access_jwt,
    mint_refresh_jwt,
)


class ContainerTestCase(TestCase):
    @patch("identity.identity.requests.get")
    def test_get_platform_jwks(self, mock_response):
        mock_response.return_value.text = json.dumps(PLATFORM_JWKS)
        get_platform_jwks()
        self.assertEqual(PLATFORM_JWKS, container.platform_jwks.export(as_dict=True))

    @patch("identity.identity.requests.get")
    @patch("identity.identity.requests.post")
    def test_attest(self, mock_response, mock_jwks_response):
        mock_jwks_response.return_value.text = json.dumps(PLATFORM_JWKS)
        urn = "org:pennlabs:example"
        access_jwt = mint_access_jwt(ID_PRIVATE_KEY, urn)
        refresh_jwt = mint_refresh_jwt(ID_PRIVATE_KEY, urn)
        mock_response.return_value.status_code = 200
        mock_response.return_value.json.return_value = {
            "access": access_jwt.serialize(),
            "refresh": refresh_jwt.serialize(),
        }
        get_platform_jwks()
        self.assertTrue(attest())
        self.assertEqual(access_jwt.serialize(), container.access_jwt.serialize())
        self.assertEqual(refresh_jwt.serialize(), container.refresh_jwt.serialize())


class ValidateUrnTestCase(TestCase):
    def test_valid_urn(self):
        validate_urn("urn:pennlabs:platform")

    def test_valid_urn_wildcard(self):
        validate_urn("urn:pennlabs:*")

    def test_invalid_urn(self):
        self.assertRaises(ImproperlyConfigured, validate_urn, "fake:pennlabs:*")

    def test_invalid_urn_wildcard(self):
        self.assertRaises(ImproperlyConfigured, validate_urn, "urn:pennlabs:penn-*")
        self.assertRaises(ImproperlyConfigured, validate_urn, "urn:*:platform")


class RefreshOutdatedTestCase(TestCase):
    def setUp(self):
        configure_container(self)

    @patch("identity.identity.requests.post")
    def test_nop(self, mock_post):
        _refresh_if_outdated()
        mock_post.assert_not_called()

    @patch("identity.identity.time")
    @patch("identity.identity.requests.post")
    def test_refresh_valid_attest(self, mock_post, mock_time):
        # Pretend access JWT is expired
        mock_time.time.return_value = time.time() + 20 * 60
        # For testing only, use existing access jwt because it's valid
        mock_post.return_value.json.return_value = {"access": container.access_jwt.serialize()}
        mock_post.return_value.status_code = 200
        _refresh_if_outdated()
        mock_post.assert_called()
        auth_headers = {"Authorization": f"Bearer {container.refresh_jwt.serialize()}"}
        mock_post.assert_called_with(REFRESH_URL, headers=auth_headers)

    @patch("identity.identity.time")
    @patch("identity.identity.requests.post")
    def test_refresh_invalid_attest(self, mock_post, mock_time):
        # Pretend access JWT is expired
        mock_time.time.return_value = time.time() + 20 * 60
        mock_post.return_value.status_code = 400
        self.assertRaises(Exception, _refresh_if_outdated)


class AuthenticatedB2BRequestTestCase(TestCase):
    def setUp(self):
        configure_container(self)

    @patch("identity.identity.requests.Session")
    def test_authorization_header(self, mock_session):
        header = {"abc": "123"}
        authenticated_b2b_request(None, None, headers=header)
        header["Authorization"] = f"Bearer {container.access_jwt.serialize()}"
        arguments = mock_session.return_value.request.call_args[1]
        self.assertEqual(header, arguments["headers"])
