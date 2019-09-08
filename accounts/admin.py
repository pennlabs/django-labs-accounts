from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect
from django.urls import reverse

from accounts.settings import accounts_settings


class LabsAdminSite(admin.AdminSite):

    def login(self, request, extra_context=None):
        if not request.user.is_authenticated:
            return redirect(reverse('accounts:login') + '?next=' + request.GET.get('next'))
        return super().login(request, extra_context)


if accounts_settings.CUSTOM_ADMIN:
    admin.site = LabsAdminSite()
    admin.site.register(Group, GroupAdmin)
    admin.site.register(User, UserAdmin)
