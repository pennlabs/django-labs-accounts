from django.urls import path

from analytics.views import JWTView, RefreshJWTView


app_name = "analytics"


urlpatterns = [
    path("jwt/attest", JWTView.as_view(), name="attest"),
    path("jwt/refresh", RefreshJWTView.as_view(), name="refresh"),
]
