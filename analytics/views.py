import requests
from django.http import HttpResponseBadRequest, HttpResponseServerError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.settings import accounts_settings


ATTEST_URL = f"{accounts_settings.PLATFORM_URL}/identity/attest/"
REFRESH_URL = f"{accounts_settings.PLATFORM_URL}/identity/refresh/"


class JWTView(APIView):
    """Returns a valid JWT response for an authenticated user"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = requests.post(
            ATTEST_URL,
            auth=(accounts_settings.CLIENT_ID, accounts_settings.CLIENT_SECRET),
        )
        if response.ok:
            content = response.json()
            return Response(
                {"access": content["access"], "refresh": content["refresh"]}
            )

        return HttpResponseServerError()


class RefreshJWTView(APIView):
    """Returns a valid JWT response for a user"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (refresh_token := request.data.get("refresh")):
            return HttpResponseBadRequest("No refresh token provided")

        auth_headers = {"Authorization": f"Bearer {refresh_token}"}
        response = requests.post(REFRESH_URL, headers=auth_headers)
        if response.ok:
            content = response.json()
            return Response({"access": content["access"]})
        else:
            return HttpResponseBadRequest("Invalid refresh token provided")
