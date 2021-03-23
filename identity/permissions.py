import json

from jwcrypto import jwt
from rest_framework import permissions

from identity.identity import container


class B2BPermission(permissions.BasePermission):
    """
    Grants permission if the current user is a superuser.
    If authentication is successful `request.product` is set
    to the urn of the product making the request.
    """

    def has_permission(self, request, view):
        authorization = request.META.get("HTTP_AUTHORIZATION")
        if authorization and " " in authorization:
            auth_type, raw_jwt = authorization.split()
            if auth_type == "Bearer":
                try:
                    validated_jwt = jwt.JWT(key=container.platform_jwks, jwt=raw_jwt)
                    claims = json.loads(validated_jwt.claims)
                    if "use" in claims and claims["use"] == "access":
                        request.product = claims["sub"]
                        return True
                except Exception:
                    return False
        return False
