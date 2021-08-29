from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.views import APIView


# Copied from django-rest-framework
# https://github.com/encode/django-rest-framework/blob/71e6c30034a1dd35a39ca74f86c371713e762c79/tests/authentication/test_authentication.py#L36  # noqa


class MockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return HttpResponse({"a": 1, "b": 2, "c": 3})

    def post(self, request):
        return HttpResponse({"a": 1, "b": 2, "c": 3})

    def put(self, request):
        return HttpResponse({"a": 1, "b": 2, "c": 3})
