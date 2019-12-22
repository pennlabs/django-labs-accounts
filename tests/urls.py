from django.contrib import admin
from django.urls import include, path
from tests.views import TestView


urlpatterns = [
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("admin/", admin.site.urls),
    path("test/", TestView.as_view(), name="test"),
]
