from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend

from accounts.settings import accounts_settings


class LabsUserBackend(RemoteUserBackend):
    def authenticate(self, request, remote_user):
        if not remote_user:
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(username=remote_user['username'])
        if created:
            user.first_name = remote_user['first_name']
            user.last_name = remote_user['last_name']
            user.email = remote_user['email']
            user.set_unusable_password()
            user.save()
            try:
                user = self.configure_user(request, user)
            except TypeError:
                user = self.configure_user(user)

        if accounts_settings.ADMIN_PERMISSION in remote_user['product_permission']:
            user.is_staff = True
            user.is_superuser = True
            user.save()
        return user if self.user_can_authenticate(user) else None
