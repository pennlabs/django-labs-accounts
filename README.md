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
    'identity.apps.IdentityConfig', # If you want to enable B2B IPC
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

(Optional) Add the new Platform DRF authentication class to rest framework's `DEFAULT_AUTHENTICATION_CLASSES`. This authentication class should go at the end of the list of authentication classes in most cases.

```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'accounts.authentication.PlatformAuthentication',
    ]
    ...
}
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

## B2B IPC

DLA also provides an interface for backend to backend IPC requests. With B2B IPC implemented, the backend of a product will—at startup time—request platform for a JWT to verify its identity. Each product will have an allow-list, and this will enable products to make requests to each other.

In order to limit a view to only be available to a B2B IPC request, you can use the included DRF permission:

```python
from identity.permissions import B2BPermission
class TestView(APIView):
    permission_classes = [B2BPermission("urn:pennlabs:example")]
```

Make sure to define an URN to limit access. Valid URNs are either a specific product (ex. `urn:pennlabs:platform`) or a wildcard (ex. `urn:pennlabs:*`)

In order to make an IPC request, use the included helper function:

```python
from identity.identity import authenticated_b2b_request
result = authenticated_b2b_request('GET', 'http://url/path')
```

## Use in Production

DLA and Penn Labs' templates are set up so that no configuration is needed to run in development. However, in production a client ID and client secret need to be set. These values should be set in vault. Contact platform for both credentials and any questions you have.

## B2B IPC

DLA also provides an interface for backend to backend IPC requests. In order to limit a view to only be available to a B2B IPC request, you can use the included DRF permission:

```python
from identity.permissions import B2BPermission

class TestView(APIView):
    permission_classes = [B2BPermission("urn:pennlabs:example")]
```

Make sure to define an URN to limit access. Valid URNs are either a specific product (ex. `urn:pennlabs:platform`) or a wildcard (ex. `urn:pennlabs:*`)

In order to make an IPC request, use the included helper function:

```python
from identity.identity import authenticated_b2b_request

result = authenticated_b2b_request('GET', 'http://url/path')
```

## Development Setup

### Install poetry:

`pipx install poetry`

### Install Dependencies:

`poetry install`

### Testing:

`export DJANGO_SETTINGS_MODULE=tests.settings && poetry run pytest`

### Linting:

`poetry run black . && poetry run isort . && poetry run flake8`

## Changelog

See [CHANGELOG.md](https://github.com/pennlabs/django-labs-accounts/blob/master/CHANGELOG.md)

## License

See [LICENSE](https://github.com/pennlabs/django-labs-accounts/blob/master/LICENSE)
