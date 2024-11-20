from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import redirect
from django.conf import settings
import requests
import re
from jwcrypto import jwt, jwk
from accounts.views import get_redirect_uri

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.EXEMPT_URLS = [
            r"^accounts/login/$",
            r"^accounts/callback/$",
            r"^accounts/logout/$",
            r"^accounts/token/$",
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
            key.import_key(**(requests.get("https://platform.pennlabs.org/accounts/.well-known/jwks.json").json()['keys'][0]))
            
            token = request.headers.get("Authorization")
            if token is None:
                return HttpResponseBadRequest(content="No Authorization header")
            
            token = token.split(" ")
            if len(token) != 2 or token[0] != "Bearer":
                return HttpResponseBadRequest(content="Invalid Authorization header")
            
            try:
                token = jwt.JWT(key=key, jwt=token[1])
            except Exception as e:
                return HttpResponseForbidden(content="Invalid token")

            return self.get_response(request)
        except Exception as e:
            print(e)            
            return HttpResponseServerError(content=str(e))