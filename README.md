# Django Labs Accounts

[![CircleCI](https://circleci.com/gh/pennlabs/django-labs-accounts.svg?style=shield)](https://circleci.com/gh/pennlabs/django-labs-accounts)
[![Coverage Status](https://codecov.io/gh/pennlabs/django-labs-accounts/branch/master/graph/badge.svg)](https://codecov.io/gh/pennlabs/django-labs-accounts)
[![PyPi Package](https://img.shields.io/pypi/v/django-labs-accounts.svg)](https://pypi.org/project/django-labs-accounts/)

## Requirements

* Python 3.6+
* Django 2.1+

## Installation

Install with pip `pip install django-labs-accounts`

Add `accounts` to `INSTALLED_APPS`

```python
INSTALLED_APPS = (
    ...
    'accounts.apps.AccountsConfig',
    ...
)
```

Add the new accounts backend to `AUTHENTICATION_BACKENDS`

```python
AUTHENTICATION_BACKENDS = (
    ...
    'accounts.backends.LabsUserBackend',
    'django.contrib.auth.backends.ModelBackend',
    ...
)
```

Add the new accounts middleware to `MIDDLEWARE`. Note the middleware does not need to be at the top of the list, but should be placed above the default Django middleware.

```python
MIDDLEWARE = [
    ...
    'accounts.middleware.OAuth2TokenMiddleware',
    ...
]
```

Add the following to `urls.py`

```python
urlpatterns = [
    ...
    path('accounts/', include('accounts.urls', namespace='accounts')),
    ...
]
```

## Documentation

All settings are handled within a `PLATFORM_ACCOUNTS` dictionary.

Example:

```python
PLATFORM_ACCOUNTS = {
    'CLIENT_ID': 'id',
    'CLIENT_SECRET': 'secret',
    'REDIRECT_URI': 'example',
    'ADMIN_PERMISSION': 'example_admin'
    'CUSTOM_ADMIN': True
}
```

The available settings are:

`CLIENT_ID` the client ID to connect to platform with. Defaults to `LABS_CLIENT_ID` environment variable.

`CLIENT_SECRET` the client secret to connect to platform with. Defaults to `LABS_CLIENT_SECRET` environment variable.

`REDIRECT_URI` the redirect uri to send to platform. Defaults to first the `LABS_REDIRECT_URI` environment variable and then generating the value from the request object.

`SCOPE` the scope for this applications tokens. Must include `introspection`. Defaults to `['read', 'introspection']`.

`PLATFORM_URL` URL of platform server to connect to. Should be `https://platform(-dev).pennlabs.org` (no trailing slash)

`ADMIN_PERMISSION` The name of the permission on platform to grant admin access. Defaults to `example_admin`

`CUSTOM_ADMIN` enable the custom admin login page to log in users through platform. Defaults to `True`

When developing locally with an http (not https) callback URL, it may be helpful to set the `OAUTHLIB_INSECURE_TRANSPORT` environment variable.

```python
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
```

## Custom post authentication

If you want to customize how DLA saves user information from platform into User objects, you can subclass `accounts.backends.LabsUserBackend` and redefine the post_authenticate method. This method will be run after the user is logged in. The parameters are:

* `user` the user object
* `created` a boolean delineating if the user was just created
* `dictionary` a dictionary of user information from platform.

Then just set the `AUTHENTICATION_BACKENDS` setting to be the subclassed backend.

Here is an example of a custom backend that sets every user's first name to `"Modified"`.

```python
from accounts.backends import LabsUserBackend

class CustomBackend(LabsUserBackend):
    def post_authenticate(self, user, created, dictionary):
        user.first_name = 'Modified'
        user.save()
```

## Use in Production

DLA and Penn Labs' templates are set up so that no configuration is needed to run in development. However, in production a client ID and client secret need to be set. These values should be set in vault. Contact platform for both credentials and any questions you have.

## Changelog

See [CHANGELOG.md](https://github.com/pennlabs/django-labs-accounts/blob/master/CHANGELOG.md)

## License

See [LICENSE](https://github.com/pennlabs/django-labs-accounts/blob/master/LICENSE)
