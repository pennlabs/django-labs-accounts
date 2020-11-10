from django.apps import AppConfig
from identity.identity import get_platform_jwks, attest


class IdentityConfig(AppConfig):
    name = "identity"
    verbose_name = "Penn Labs Service Identity"

    def ready(self):
        get_platform_jwks()
        attest()
