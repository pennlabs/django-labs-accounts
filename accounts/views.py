from requests_oauthlib import OAuth2Session
from django.contrib import auth
from django.http import HttpResponseServerError
from django.shortcuts import redirect
from django.views import View
from accounts.settings import CLIENT_ID, CLIENT_SECRET, PLATFORM_URL, REDIRECT_URI, SCOPE


class LoginView(View):
    def get(self, request):
        request.session.__setitem__('next', request.GET.get('next'))
        if not request.user.is_authenticated:
            platform = OAuth2Session(CLIENT_ID, scope=SCOPE, redirect_uri=REDIRECT_URI)
            authorization_url, state = platform.authorization_url(PLATFORM_URL + '/accounts/authorize/')
            response = redirect(authorization_url)
            request.session.__setitem__('state', state)
            return response
        return redirect(request.session.pop('next'))


class CallbackView(View):
    def get(self, request):
        code = request.GET.get('code')
        state = request.session.pop('state')
        platform = OAuth2Session(CLIENT_ID, state=state)
        token = platform.fetch_token(
            PLATFORM_URL + '/accounts/token/',
            client_secret=CLIENT_SECRET,
            authorization_response=request.get_full_path()
        )
        platform = OAuth2Session(CLIENT_ID, token=token)
        access_token = token['access_token']
        uuid = platform.get(PLATFORM_URL + '/accounts/introspect/?token=' + access_token).json()['uuid']
        user = auth.authenticate(remote_user=uuid)
        if user:
            auth.login(request, user)
            return redirect(request.session.pop('next'))
        return HttpResponseServerError()
