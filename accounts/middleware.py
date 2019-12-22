import requests
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden

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
                    data = requests.post(
                        url=accounts_settings.PLATFORM_URL + "/accounts/introspect/",
                        headers=headers,
                        data=body,
                    )
                    if data.status_code == 200:  # Access token is valid
                        data = data.json()
                        user = User.objects.filter(id=int(data["user"]["pennid"]))
                        if len(user) == 1:  # User has an account on this product
                            request.user = user.first()
                    else:  # Access token is invalid
                        return HttpResponseForbidden()
                except requests.exceptions.RequestException:  # Can't connect to platform
                    # Throw a 403 because we can't verify the incoming access token so we
                    # treat it as invalid. Ideally platform will never go down, so this
                    # should never happen.
                    return HttpResponseForbidden()

        response = self.get_response(request)
        return response
