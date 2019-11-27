from datetime import timedelta

import requests
from django.utils import timezone

from accounts.settings import accounts_settings


def authenticated_request(user, method, url,
                          params=None, data=None, headers=None, cookies=None, files=None,
                          auth=None, timeout=None, allow_redirects=True, proxies=None,
                          hooks=None, stream=None, verify=None, cert=None, json=None):
    """
    Helper method to make an authenticated request using the user's access token
    NOTE be ABSOLUTELY sure you only make a request to Penn Labs products, otherwise
    you will expose user's access tokens to the URL you provide and bad things will
    happen
    """

    # Access token is expired. Try to refresh access token
    if user.accesstoken.expires_at < timezone.now():
        if not refresh_access_token(user):
            return None  # Couldn't update access token

    # Update Headers
    headers = headers or {}
    headers['Authorization'] = f'Bearer {user.accesstoken.token}'

    # Make request
    s = requests.Session()
    return s.request(
        method=method,
        url=url,
        params=params,
        data=data,
        headers=headers,
        cookies=cookies,
        files=files,
        auth=None,
        timeout=None,
        allow_redirects=allow_redirects,
        proxies=proxies,
        hooks=hooks,
        stream=stream,
        verify=verify,
        cert=cert,
        json=json,
    )


def refresh_access_token(user):
    """
    Helper method to update a user's access token. Should be used when a user's
    access token has expired, but still has a valid refresh token
    """
    body = {
        'grant_type': 'refresh_token',
        'client_id': accounts_settings.CLIENT_ID,
        'client_secret': accounts_settings.CLIENT_SECRET,
        'refresh_token': user.refreshtoken.token,
    }
    try:
        data = requests.post(
            url=accounts_settings.PLATFORM_URL + '/accounts/token/',
            data=body
        )
        if data.status_code == 200:  # Access token refreshed successfully
            data = data.json()
            # Update Access token
            user.accesstoken.token = data['access_token']
            user.accesstoken.expires_at = timezone.now() + timedelta(seconds=data['expires_in'])
            user.accesstoken.save()

            # Update Refresh Token
            user.refreshtoken.token = data['refresh_token']
            user.refreshtoken.save()

    except requests.exceptions.RequestException:  # Can't connect to platform
        return False
    return True
