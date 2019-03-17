import os
from django.conf import settings

CLIENT_ID = getattr(settings, "OAUTH2_CLIENT_ID", os.environ.get('OAUTH2_CLIENT_ID'))
CLIENT_SECRET = getattr(settings, "OAUTH2_CLIENT_SECRET", os.environ.get('OAUTH2_CLIENT_ID'))
REDIRECT_URI = getattr(settings, "OAUTH2_REDIRECT_URI", os.environ.get('OAUTH2_REDIRECT_URI'))
SCOPE = getattr(settings, "OAUTH2_SCOPES", ['read', 'introspection'])
PLATFORM_URL = getattr(settings, "OAUTH2_PLATFORM_URL", 'https://platform.pennlabs.org')

USER_SETTINGS = getattr(settings, "PLATFORM_ACCOUNTS", {})
