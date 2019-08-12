from django.contrib import auth
from django.http import HttpResponseServerError
from django.http.response import HttpResponseBadRequest
from django.shortcuts import redirect
from django.views import View
from requests_oauthlib import OAuth2Session

from accounts.settings import accounts_settings


class LoginView(View):
    def get(self, request):
        return_to = request.GET.get('next')
        if not return_to:
            return HttpResponseBadRequest('Invalid next parameter')
        request.session.__setitem__('next', return_to)
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
            request.session.__setitem__('state', state)
            return response
        return redirect(request.session.pop('next'))


class CallbackView(View):
    def get(self, request):
        state = request.session.pop('state')
        platform = OAuth2Session(accounts_settings.CLIENT_ID, state=state)
        token = platform.fetch_token(
            accounts_settings.PLATFORM_URL + '/accounts/token/',
            client_secret=accounts_settings.CLIENT_SECRET,
            authorization_response=request.build_absolute_uri()
        )
        platform = OAuth2Session(accounts_settings.CLIENT_ID, token=token)
        access_token = token['access_token']
        introspect_url = accounts_settings.PLATFORM_URL + '/accounts/introspect/?token=' + access_token
        user_props = platform.get(introspect_url).json()['user']
        user = auth.authenticate(request, remote_user=user_props)
        if user:
            auth.login(request, user)
            return redirect(request.session.pop('next'))
        return HttpResponseServerError()


class LogoutView(View):
    def get(self, request):
        auth.logout(request)
        return redirect('/')
