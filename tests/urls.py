from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('admin/', admin.site.urls),
]
