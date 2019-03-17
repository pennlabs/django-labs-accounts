Django Labs Accounts
====================

Requirements
------------

Installation
------------
Install with pip
    pip install django-labs-accounts

Add `accounts` to `INSTALLED_APPS`
.. code-block:: python

    INSTALLED_APPS = (
        ...
        'accounts.apps.AccountsConfig',
    )

Add the following to `urls.py`
.. code-block:: python

    urlpatterns = [
        ...
        path('accounts/', include('accounts.urls', namespace='accounts'))
    ]

Documentation
-------------
TODO

Changelog
---------
See `CHANGELOG.md <https://github.com/pennlabs/django-labs-accounts/blob/master/CHANGELOG.md>`_.

License
-------
Licensed See `LICENSE.md <https://github.com/pennlabs/django-labs-accounts/blob/master/LICENSE.md>`_.
