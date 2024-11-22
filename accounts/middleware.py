import re

import requests
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseServerError,
)
from django.shortcuts import redirect
from jwcrypto import jwk, jwt

from accounts.views import get_redirect_uri


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.EXEMPT_URLS = [
            r"^/accounts/login/$",
            r"^/accounts/callback/$",
            r"^/accounts/logout/$",
            r"^/accounts/token/$",
            r"^/admin/.*$",
        ]

    def handle_no_permission(self, request):
        return redirect(get_redirect_uri(request))

    def add_new_exempt_urls(self):
        pass
        # EXAMPLE USAGE
        # self.EXEMPT_URLS.append(r"^accounts/new_exempt_url/$")
        # This can be overriden in the subclass

    def __call__(self, request):
        self.add_new_exempt_urls()
        regex_list = [re.compile(url) for url in self.EXEMPT_URLS]
        if any(url.match(request.path) for url in regex_list):
            return self.get_response(request)

        try:
            key = jwk.JWK()
            key.import_key(
                **(
                    requests.get(
                        "https://platform.pennlabs.org/accounts/.well-known/jwks.json"
                    ).json()["keys"][0]
                )
            )

            token = request.headers.get("Authorization")
            if token is None:
                response = HttpResponseBadRequest(content="No Authorization header")
                response.status_code = 401
                return response

            token = token.split(" ")
            if len(token) != 2 or token[0] != "Bearer":
                response = HttpResponseBadRequest(
                    content="Invalid Authorization header"
                )
                response.status_code = 401
                return response

            try:
                token = jwt.JWT(key=key, jwt=token[1])
            except Exception as e:
                response = HttpResponseForbidden(content=f"Invalid token: {e}")
                response.status_code = 401
                return response

            return self.get_response(request)
        except Exception as e:
            print(e)
            return HttpResponseServerError(content=str(e))
