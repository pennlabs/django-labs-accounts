import datetime

import requests
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from requests_oauthlib import OAuth2Session

from accounts.models import AccessToken, RefreshToken
from accounts.settings import accounts_settings


User = get_user_model()


def invalid_next(return_to):
    try:
        from sentry_sdk import capture_message

        capture_message(f"Invalid next parameter: '{return_to}'", level="error")
    except ImportError:
        pass


def get_redirect_uri(request):
    """
    Determine the redirect URI using either an environment variable or the request.
    """
    if accounts_settings.REDIRECT_URI:
        return accounts_settings.REDIRECT_URI
    return request.build_absolute_uri(reverse("accounts:callback"))


class LoginView(View):
    """
    Log in the user and redirect to next query parameter
    """

    def get(self, request):
        return_to = request.GET.get("next", "/")
        if not return_to.startswith("/"):
            invalid_next(return_to)
            return_to = "/"
        request.session["next"] = return_to
        if not request.user.is_authenticated:
            platform = OAuth2Session(
                accounts_settings.CLIENT_ID,
                scope=accounts_settings.SCOPE,
                redirect_uri=get_redirect_uri(request),
            )
            authorization_url, state = platform.authorization_url(
                accounts_settings.PLATFORM_URL + "/accounts/authorize/"
            )
            response = redirect(authorization_url)
            request.session["state"] = state
            return response
        return redirect(return_to)


class CallbackView(View):
    """
    View where the the user is redirected to from platform with the
    query parameter code being that user's Authorization Code
    """

    def get(self, request):
        return_to = request.session.pop("next", "/")
        if not return_to.startswith("/"):
            invalid_next(return_to)
            return_to = "/"
        state = request.session.pop("state")
        platform = OAuth2Session(
            accounts_settings.CLIENT_ID,
            redirect_uri=get_redirect_uri(request),
            state=state,
        )

        # Get the user's access and refresh tokens
        token = platform.fetch_token(
            accounts_settings.PLATFORM_URL + "/accounts/token/",
            client_secret=accounts_settings.CLIENT_SECRET,
            authorization_response=request.build_absolute_uri(),
        )

        # Use the access token to log in the user using information from platform
        platform = OAuth2Session(accounts_settings.CLIENT_ID, token=token)
        introspect_url = accounts_settings.PLATFORM_URL + "/accounts/introspect/"
        platform_request = platform.post(
            introspect_url, data={"token": token["access_token"]}
        )
        if platform_request.status_code == 200:  # Connected to platform successfully
            user_props = platform_request.json()["user"]
            user_props["token"] = token
            user = auth.authenticate(request, remote_user=user_props)
            if user:
                auth.login(request, user)
                return redirect(return_to)
        return HttpResponseServerError()


class LogoutView(View):
    """
    Log out the user and redirect to next query parameter
    """

    def get(self, request):
        auth.logout(request)
        return_to = request.GET.get("next", "/")
        if not return_to.startswith("/"):
            invalid_next(return_to)
            return_to = "/"
        return redirect(return_to)


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):
    """
    View for token-based authentication, specifically for mobile products that
    do not rely on session authentication.

    Assumes OAuth2 Authorization code has been retrieved prior to accessing this route.
    """

    def post(self, request):
        # Hit Platform OAuth2 token provider
        token_url = accounts_settings.PLATFORM_URL + "/accounts/token/"
        response = requests.post(token_url, data=request.POST.dict())
        if response.status_code == 200:
            token = response.json()
            # Use the access token to retrieve user information from platform
            platform = OAuth2Session(accounts_settings.CLIENT_ID, token=token)
            introspect_url = accounts_settings.PLATFORM_URL + "/accounts/introspect/"
            platform_request = platform.post(
                introspect_url, data={"token": token["access_token"]}
            )
            if (
                platform_request.status_code == 200
            ):  # Connected to platform successfully
                user_props = platform_request.json()["user"]
                # Retrieve or create user object from Platform response
                user = auth.authenticate(request, remote_user=user_props, tokens=False)
                if not user:
                    return JsonResponse({"detail": "Invalid User"}, status=400)
                # Update user Access and Refresh tokens
                AccessToken.objects.update_or_create(
                    user=user,
                    defaults={
                        "expires_at": timezone.now()
                        + datetime.timedelta(seconds=token["expires_in"]),
                        "token": token["access_token"],
                    },
                )
                RefreshToken.objects.update_or_create(
                    user=user, defaults={"token": token["refresh_token"]}
                )
                return JsonResponse(response.json())
            return JsonResponse({"detail": "Invalid tokens"}, status=403)
        return JsonResponse({"detail": "Invalid parameters"}, status=400)
