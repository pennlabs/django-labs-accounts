from django.urls import path

from accounts.views import CallbackView, LoginView, LogoutView, TokenView


app_name = "accounts"


urlpatterns = [
    path("callback/", CallbackView.as_view(), name="callback"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/", TokenView.as_view(), name="token"),
]
