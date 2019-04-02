from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend


class LabsUserBackend(RemoteUserBackend):
    def authenticate(self, request, remote_user):
        if not remote_user:
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(uuid=remote_user)
        if created:
            user.username = user.uuid
            user.set_unusable_password()
            user.save()
            try:
                user = self.configure_user(request, user)
            except TypeError:
                user = self.configure_user(user)

        return user if self.user_can_authenticate(user) else None
