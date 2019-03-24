import sys
import django
from django.conf import settings
from django.test.runner import DiscoverRunner

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    ROOT_URLCONF='tests.urls',
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'accounts.apps.AccountsConfig',
    ),
    AUTH_USER_MODEL='accounts.User',
    AUTHENTICATION_BACKENDS=(
        'accounts.backends.LabsUserBackend',
        'django.contrib.auth.backends.ModelBackend',
    ),
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ],
    PLATFORM_ACCOUNTS={
        'CLIENT_ID': 'id',
        'CLIENT_SECRET': 'secret',
        'REDIRECT_URI': 'example',
    }
)


django.setup()
test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['tests'])
if failures:
    sys.exit(failures)
