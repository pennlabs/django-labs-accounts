from django.conf import settings
from django.contrib import auth
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.http.response import HttpResponseBadRequest
from django.shortcuts import redirect
from django.views import View
from requests_oauthlib import OAuth2Session

from accounts.settings import accounts_settings


class LoginView(View):
    """
    Log in the user and redirect to next query parameter
    """
    def get(self, request):
        return_to = request.GET.get('next')
        if not return_to:
            return HttpResponseBadRequest('Invalid next parameter')
        request.session['next'] = return_to
        if not request.user.is_authenticated:
            platform = OAuth2Session(
                accounts_settings.CLIENT_ID,
                scope=accounts_settings.SCOPE,
                redirect_uri=accounts_settings.REDIRECT_URI
            )
            authorization_url, state = platform.authorization_url(
                accounts_settings.PLATFORM_URL + '/accounts/authorize/'
            )
            response = redirect(authorization_url)
            request.session['state'] = state
            return response
        return redirect(request.session.pop('next', '/'))


class CallbackView(View):
    """
    View where the the user is redirected to from platform with the
    query parameter code being that user's Authorization Code
    """
    def get(self, request):
        response = HttpResponseRedirect(request.session.pop('next'))
        state = request.session.pop('state')
        platform = OAuth2Session(accounts_settings.CLIENT_ID, redirect_uri=accounts_settings.REDIRECT_URI, state=state)

        # Get the user's access and refresh tokens
        token = platform.fetch_token(
            accounts_settings.PLATFORM_URL + '/accounts/token/',
            client_secret=accounts_settings.CLIENT_SECRET,
            authorization_response=request.build_absolute_uri()
        )

        # Use the access token to log in the user using information from platform
        platform = OAuth2Session(accounts_settings.CLIENT_ID, token=token)
        introspect_url = accounts_settings.PLATFORM_URL + '/accounts/introspect/'
        user_props = platform.post(introspect_url, data={'token': token['access_token']}).json()['user']
        user_props['token'] = token
        user_props['pennid'] = int(user_props['pennid'])
        user = auth.authenticate(request, remote_user=user_props)
        if user:
            auth.login(request, user)
            return response
        return HttpResponseServerError()


class LogoutView(View):
    """
    Log out the user and redirect to next query parameter
    """
    def get(self, request):
        auth.logout(request)
        return redirect(request.GET.get('next', '/'))
