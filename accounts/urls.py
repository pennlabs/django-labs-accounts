from django.urls import path
from accounts.views import CallbackView, LoginView


app_name = 'accounts'


urlpatterns = [
    path('callback/', CallbackView.as_view(), name='callback'),
    path('login/', LoginView.as_view(), name='login'),
]
