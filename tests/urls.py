from django.contrib import admin
from django.urls import include, path

from accounts.authentication import PlatformAuthentication
from tests.views import MockView


urlpatterns = [
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("admin/", admin.site.urls),
    path("token/", MockView.as_view(authentication_classes=[PlatformAuthentication])),
]
