import requests
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden, HttpResponseServerError

from accounts.settings import accounts_settings


User = get_user_model()


class OAuth2TokenMiddleware:
    """
    When a view is requested using a Bearer Authorization header,
    check and set request.user to the owner of said token
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        authorization = request.META.get("HTTP_AUTHORIZATION")
        if authorization and " " in authorization:
            auth_type, token = authorization.split()
            if auth_type == "Bearer":  # Only validate if Authorization header type is Bearer
                body = {"token": token}
                headers = {"Authorization": "Bearer {}".format(token)}
                try:
                    platform_request = requests.post(
                        url=accounts_settings.PLATFORM_URL + "/accounts/introspect/",
                        headers=headers,
                        data=body,
                    )
                    if platform_request.status_code == 200:  # Access token is valid
                        json = platform_request.json()
                        user_props = json["user"]
                        # TODO: maybe update access token if a local one does not exist
                        # user_props["token"] = {
                        #     "access_token": token,
                        #     "refresh_token": "",
                        #     "expires_in": json["exp"] - int(timezone.now().timestamp()),
                        # }
                        user = auth.authenticate(remote_user=user_props, tokens=False)
                        if user:  # User authenticated successfully
                            request.user = user
                        else:  # Error occurred
                            return HttpResponseServerError()
                    else:  # Access token is invalid
                        return HttpResponseForbidden()
                except requests.exceptions.RequestException:  # Can't connect to platform
                    # Throw a 403 because we can't verify the incoming access token so we
                    # treat it as invalid. Ideally platform will never go down, so this
                    # should never happen.
                    return HttpResponseForbidden()

        response = self.get_response(request)
        return response
