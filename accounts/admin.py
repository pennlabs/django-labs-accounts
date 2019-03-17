from django.contrib import admin
from accounts.models import User


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('uuid',)


admin.site.register(User, UserAdmin)
