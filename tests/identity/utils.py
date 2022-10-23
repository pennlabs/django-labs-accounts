import json
import time

from jwcrypto import jwk, jwt

from identity.identity import container


PLATFORM_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQCbCYh5h2NmQuBqVO6G+/CO+cHm9VBzsb0MeA6bbQfDnbhstVOT
j0hcnZJzDjYc6ajBZZf6gxVP9xrdm9Uh599VI3X5PFXLbMHrmzTAMzCGIyg+/fnP
0gocYxmCX2+XKyj/Zvt1pUX8VAN2AhrJSfxNDKUHERTVEV9bRBJg4F0C3wIDAQAB
AoGAP+i4nNw+Ec/8oWh8YSFm4xE6qKG0NdTtSMAOyWwy+KTB+vHuT1QPsLn1vj77
+IQrX/moogg6F1oV9YdA3vat3U7rwt1sBGsRrLhA+Spp9WEQtglguNo4+QfVo2ju
YBa2rG+h75qjiA3xnU//F3rvwnAsOWv0NUVdVeguyR+u6okCQQDBUmgWeH2WHmUn
2nLNCz+9wj28rqhfOr9Ptem2gqk+ywJmuIr4Y5S1OdavOr2UZxOcEwncJ/MLVYQq
MH+x4V5HAkEAzU2GMR5OdVLcxfVTjzuIC76paoHVWnLibd1cdANpPmE6SM+pf5el
fVSwuH9Fmlizu8GiPCxbJUoXB/J1tGEKqQJBALhClEU+qOzpoZ6/voYi/6kdN3zc
uEy0EN6n09AKb8gS9QH1STgAqh+ltjMkeMe3C2DKYK5/QU9/Pc58lWl1FkcCQG67
ZamQgxjcvJ85FvymS1aqW45KwNysIlzHjFo2jMlMf7dN6kobbPMQftDENLJvLWIT
qoFyGycdsxZiPAIyZSECQQCZFn3Dl6hnJxWZH8Fsa9hj79kZ/WVkIXGmtdgt0fNr
dTnvCVtA59ne4LEVie/PMH/odQWY0SxVm/76uBZv/1vY
-----END RSA PRIVATE KEY-----"""

SIGNING_ALG = "RS256"
EXPIRY_TIME = 15 * 60  # 15 minutes
ID_PRIVATE_KEY = jwk.JWK.from_pem(PLATFORM_PRIVATE_KEY.encode("utf-8"))

PLATFORM_JWKS = {
    "keys": [{"alg": SIGNING_ALG, "use": "sig", "kid": ID_PRIVATE_KEY.thumbprint()}]
}
PLATFORM_JWKS["keys"][0].update(json.loads(ID_PRIVATE_KEY.export_public()))

# Taken from platform


def mint_access_jwt(key: jwk.JWK, urn: str) -> jwt.JWT:
    """
    Mint a JWT with the following claims:
    - use -> access - this says that this JWT is strictly an access JWT
    - iat -> now - this says that this JWT isn't active until the current time.
    this protects us from attacks from clock skew
    - exp -> expiry_time - this makes sure our JWT is only valid for EXPIRY_TIME
    """
    now = time.time()
    expiry_time = now + EXPIRY_TIME
    token = jwt.JWT(
        header={"alg": SIGNING_ALG},
        claims={"sub": urn, "use": "access", "iat": now, "exp": expiry_time},
    )
    token.make_signed_token(key)
    return token


def mint_refresh_jwt(key: jwk.JWK, urn: str) -> jwt.JWT:
    """
    Mint a JWT with the following claims:
    - use -> refresh - this says that this JWT is strictly a refresh JWT
    - iat -> now - this says that this JWT isn't active until the current time.
      this protects us from attacks from clock skew
    - no exp claim because refresh JWTs do not expire
    """
    now = time.time()
    token = jwt.JWT(
        header={"alg": SIGNING_ALG}, claims={"sub": urn, "use": "refresh", "iat": now}
    )
    token.make_signed_token(key)
    return token


def configure_container(self):
    """
    Configure variables locally for testing
    """
    self.urn = "urn:pennlabs:example"
    container.platform_jwks = jwk.JWKSet.from_json(json.dumps(PLATFORM_JWKS))
    refresh_jwt = mint_refresh_jwt(ID_PRIVATE_KEY, self.urn)
    container.refresh_jwt = jwt.JWT(
        key=container.platform_jwks, jwt=refresh_jwt.serialize()
    )
    access_jwt = mint_access_jwt(ID_PRIVATE_KEY, self.urn)
    container.access_jwt = jwt.JWT(
        key=container.platform_jwks, jwt=access_jwt.serialize()
    )