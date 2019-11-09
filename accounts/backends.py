from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend

from accounts.settings import accounts_settings


class LabsUserBackend(RemoteUserBackend):
    def authenticate(self, request, remote_user):
        """
        Authenticate a user given a dictionary of user information from
        platform.
        """
        if not remote_user:
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(
            id=remote_user['pennid'],
            defaults={'username': remote_user['username']}
        )

        if created:
            user.set_unusable_password()
            user.save()
            try:
                user = self.configure_user(request, user)
            except TypeError:
                user = self.configure_user(user)

        # Update user fields if changed
        for field in ['first_name', 'last_name', 'username', 'email']:
            if getattr(user, field) is not remote_user[field]:
                setattr(user, field, remote_user[field])

        if accounts_settings.ADMIN_PERMISSION in remote_user['product_permission']:
            user.is_staff = True
            user.is_superuser = True

        user.save()
        self.post_authenticate(user, created, remote_user)
        return user if self.user_can_authenticate(user) else None

    def post_authenticate(self, user, created, dictionary):
        """
        Post Authentication method that is run after logging in a user.
        This allows products to add custom configuration by subclassing
        LabsUserBackend and modifying this method.
        By default this does nothing.
        """
        pass
