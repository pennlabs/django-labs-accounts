Django Labs Accounts
====================
.. image:: https://img.shields.io/circleci/project/github/pennlabs/django-labs-accounts/master.svg
    :target: https://circleci.com/gh/pennlabs/django-labs-accounts
.. image:: https://coveralls.io/repos/github/pennlabs/django-labs-accounts/badge.svg?branch=feature%2Fsettings
    :target: https://coveralls.io/github/pennlabs/django-labs-accounts?branch=feature%2Fsettings
.. image:: https://img.shields.io/pypi/v/django-labs-accounts.svg
    :target: https://pypi.org/project/django-labs-accounts/

Requirements
------------
* Python 3.4+
* Django 2.0+

Installation
------------
Install with pipenv
    pipenv install django-labs-accounts

Add ``accounts`` to ``INSTALLED_APPS``

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'accounts.apps.AccountsConfig',
    )

Add the following to ``urls.py``

.. code-block:: python

    urlpatterns = [
        ...
        path('accounts/', include('accounts.urls', namespace='accounts'))
    ]

Documentation
-------------
All settings are handled with a ``PLATFORM_ACCOUNTS`` dictionary.

Example:

.. code-block:: python

    PLATFORM_ACCOUNTS = {
        'CLIENT_ID': 'id',
        'CLIENT_SECRET': 'secret',
        'REDIRECT_URI': 'example',
    }

The available settings are:

``CLIENT_ID`` the client ID to connect to platform with. Defaults to ``LABS_CLIENT_ID`` environment variable.

``CLIENT_SECRET`` the client secret to connect to platform with. Defaults to ``LABS_CLIENT_SECRET`` environment variable.

``REDIRECT_URI`` the redirect uri to send to platform. Defaults to ``LABS_REDIRECT_URI`` environment variable.

``SCOPE`` the scope for this applications tokens. Must include ``introspection``. Defaults to ``['read', 'introspection']``.

``PLATFORM_URL`` URL of platform server to connect to. Should be ``https://platform(-dev).pennlabs.org`` (no trailing slash)

Changelog
---------
See `CHANGELOG.md <https://github.com/pennlabs/django-labs-accounts/blob/master/CHANGELOG.md>`_.

License
-------
Licensed See `LICENSE.md <https://github.com/pennlabs/django-labs-accounts/blob/master/LICENSE.md>`_.
