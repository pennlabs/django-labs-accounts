import json
import time
from unittest.mock import patch

from django.test import TestCase

from identity.identity import (
    REFRESH_URL,
    _refresh_if_outdated,
    attest,
    authenticated_b2b_request,
    container,
    get_platform_jwks,
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
        mock_response.return_value.json.return_value = {
            "access": access_jwt.serialize(),
            "refresh": refresh_jwt.serialize(),
        }
        get_platform_jwks()
        attest()
        self.assertEqual(access_jwt.serialize(), container.access_jwt.serialize())
        self.assertEqual(refresh_jwt.serialize(), container.refresh_jwt.serialize())


class RefreshOutdatedTestCase(TestCase):
    def setUp(self):
        configure_container(self)

    @patch("identity.identity.requests.get")
    def test_nop(self, mock_get):
        _refresh_if_outdated()
        mock_get.assert_not_called()

    @patch("identity.identity.time")
    @patch("identity.identity.requests.get")
    def test_refresh(self, mock_get, mock_time):
        # Pretend access JWT is expired
        mock_time.time.return_value = time.time() + 20 * 60
        # For testing only, use existing access jwt because it's valid
        mock_get.return_value.json.return_value = {"access": container.access_jwt.serialize()}
        _refresh_if_outdated()
        mock_get.assert_called()
        auth_headers = {"Authorization": f"Bearer {container.refresh_jwt.serialize()}"}
        mock_get.assert_called_with(REFRESH_URL, headers=auth_headers)


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
