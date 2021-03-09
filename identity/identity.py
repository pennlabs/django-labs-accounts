from jwcrypto import jwt, jwk
import requests
import time
import json

from accounts.settings import accounts_settings


JWKS_URL = f"{accounts_settings.PLATFORM_URL}/identity/jwks/"
ATTEST_URL = f"{accounts_settings.PLATFORM_URL}/identity/attest/"
REFRESH_URL = f"{accounts_settings.PLATFORM_URL}/identity/refresh/"


class IdentityContainer:
    refresh_jwt: jwt.JWT = None
    access_jwt: jwt.JWT = None
    platform_jwks: jwk.JWKSet = None


container = IdentityContainer()


def get_platform_jwks():
    """
    Download the JWKS from Platform to verify JWTS
    """

    try:
        response = requests.get(JWKS_URL)
        content = response.json()
        # For some reason this method wants a raw string instead of a python dictionary
        container.platform_jwks = jwk.JWKSet.from_json(response.text)
    except Exception:
        container.platform_jwks = None


def attest():
    """
    Perform the initial authentication (attest) with Platform using the Client ID
    and Secret from DOT
    """

    response = requests.post(
        ATTEST_URL, auth=(accounts_settings.CLIENT_ID, accounts_settings.CLIENT_SECRET)
    )
    content = response.json()
    container.access_jwt = jwt.JWT(key=container.platform_jwks, jwt=content["access"])
    container.refresh_jwt = jwt.JWT(key=container.platform_jwks, jwt=content["refresh"])


def refresh_if_outdated():
    access_claims = json.loads(container.access_jwt.claims)
    # only continue if our access jwt is expired
    if time.time() < access_claims["exp"]:
        return

    auth_headers = {"Authorization": f"Bearer {container.refresh_jwt.serialize()}"}
    response = requests.get(REFRESH_URL, headers=auth_headers)
    content = response.json()
    container.access_jwt = jwt.JWT(key=container.platform_jwks, jwt=content["access"])


# structure copied from:
# https://github.com/psf/requests/blob/2f70990cd3fabf7b05cb9a69b3dab1a43bbf0096/requests/api.py#L64
def get(url, params=None, **kwargs):
    if "headers" not in kwargs:
        kwargs["headers"] = {}
    kwargs["headers"]["Authorization"] = f"Bearer {container.access_jwt.serialize()}"
    return requests.get(url, params=params, **kwargs)


# structure copied from:
# https://github.com/psf/requests/blob/2f70990cd3fabf7b05cb9a69b3dab1a43bbf0096/requests/api.py#L107
def post(url, data=None, json=None, **kwargs):
    if "headers" not in kwargs:
        kwargs["headers"] = {}
    kwargs["headers"]["Authorization"] = f"Bearer {container.access_jwt.serialize()}"
    return requests.post(url, data=data, json=json, **kwargs)
