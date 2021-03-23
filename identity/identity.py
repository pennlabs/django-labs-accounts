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


def _refresh_if_outdated():
    """
    Refresh the access jwt if it is expired.
    """
    access_claims = json.loads(container.access_jwt.claims)
    # only continue if our access jwt is expired
    if time.time() < access_claims["exp"]:
        return

    auth_headers = {"Authorization": f"Bearer {container.refresh_jwt.serialize()}"}
    response = requests.get(REFRESH_URL, headers=auth_headers)
    content = response.json()
    container.access_jwt = jwt.JWT(key=container.platform_jwks, jwt=content["access"])


def authenticated_b2b_request(
    method,
    url,
    params=None,
    data=None,
    headers=None,
    cookies=None,
    files=None,
    auth=None,
    timeout=None,
    allow_redirects=True,
    proxies=None,
    hooks=None,
    stream=None,
    verify=None,
    cert=None,
    json=None,
):
    """
    Helper method to make an authenticated b2b request NOTE be ABSOLUTELY sure you
    only make a request to Penn Labs products, otherwise you will expose credentials
    and bad things will happen
    """

    # Attempt refresh
    _refresh_if_outdated()

    # Update Headers
    headers = {} if headers is None else headers
    headers["Authorization"] = f"Bearer {container.access_jwt.serialize()}"

    # Make the request
    # We're only using a session to provide an easy wrapper to define the http method
    # GET, POST, etc in the method call.
    s = requests.Session()
    return s.request(
        method=method,
        url=url,
        params=params,
        data=data,
        headers=headers,
        cookies=cookies,
        files=files,
        auth=None,
        timeout=None,
        allow_redirects=allow_redirects,
        proxies=proxies,
        hooks=hooks,
        stream=stream,
        verify=verify,
        cert=cert,
        json=json,
    )
