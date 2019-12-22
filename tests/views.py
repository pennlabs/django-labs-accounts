from django.http import HttpResponse
from django.views import View


class TestView(View):
    def get(self, request):
        return HttpResponse("Success")
