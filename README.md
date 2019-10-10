# Django Labs Accounts

[![CircleCI](https://circleci.com/gh/pennlabs/django-labs-accounts.svg?style=shield)](https://circleci.com/gh/pennlabs/django-labs-accounts)
[![Coverage Status](https://coveralls.io/repos/github/pennlabs/django-labs-accounts/badge.svg?branch=master)](https://coveralls.io/github/pennlabs/django-labs-accounts?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/django-labs-accounts.svg)](https://pypi.org/project/django-labs-accounts/)

## Requirements

* Python 3.5+
* Django 2.0+

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

`REDIRECT_URI` the redirect uri to send to platform. Defaults to `LABS_REDIRECT_URI` environment variable.

`SCOPE` the scope for this applications tokens. Must include `introspection`. Defaults to `['read', 'introspection']`.

`PLATFORM_URL` URL of platform server to connect to. Should be `https://platform(-dev).pennlabs.org` (no trailing slash)

`ADMIN_PERMISSION` The name of the permission on platform to grant admin access. Defaults to `example_admin`

`CUSTOM_ADMIN` enable the custom admin login page to log in users through platform. Defaults to `True`

When developing locally with an http (not https) callback URL, it may be helpful to set the `OAUTHLIB_INSECURE_TRANSPORT` environment variable.

```python
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
```

## Changelog

See [CHANGELOG.md](https://github.com/pennlabs/django-labs-accounts/blob/master/CHANGELOG.md)

## License

See [LICENSE.md](https://github.com/pennlabs/django-labs-accounts/blob/master/LICENSE.md)
