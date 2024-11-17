import requests
from django.contrib import auth
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from accounts.settings import accounts_settings
from identity.identity import get_validated_claims

from jose import jwt, jwk, JWTError

User = get_user_model()

LABS_PLATFORM_JWK = {
    "alg": "RS256",
    "use": "sig",
    "kid": "gbhhvs2dS_cCr607KsoY3v0Mv1iFRdQEvgl_IEJf0Gc",
    "e": "AQAB",
    "kty": "RSA",
    "n": "0uNjV3JmujIInNv64phIcaZ9Uma9oEKgxBGILMMgt0Pa9WJZMKj8BGmuftOl4uKtW5LLu5L6Qd0aAXvvATNalk8hB4Oq3HGACsizYNcdMAmSTvr6rzeihX8mVkhSQ3q00mv2hPC_nYJjVPA4UYXXjoztdSRibYXu7LyGOATHmhCh-qb-MAFHOmjV3j-ei4mTF-eYEdzd0sG44cGR1NOb1aOHYkS6Qry9b9K-XRLevRIW605dixv2c7plDN-B4gWzImaI9MSK3qxsfF6fOqiz4IHayInulMRknQSAIPvN0_Ybkd4VnQ-AmBp19dTHM4HgDAhxCt0V2tVUUUHsOxCxDsR7s7lF6rcvVuWQfImz1zgO-N3Sz76qtlKjbHtVaGc6tURzNKAYNWKAk3C_VL2OUI5B7jt6pjU43YqEZyffhDNR6Y_uWYo9sgQ6-LJOLP_9zcVr0tlXfLFmb4QamgFBrqa2zHw30oQttZG-B8eRmj4YeFMQNhlH-EMLGDq7vpjCRhNhV36TZMdpCT5rxlZmbP-zR4DTbRJaE6ZG_oPHZllAWiRkOJvTueRUzVNhPlULpojE3RF5tNyZPBoImKAzbKIAXXnz0vRsLI-apTlbB4CwnT_fXh9mjHsS_4kPPZtGcnP9RtEABOVJ4zM-D_MCfrdpPYJ_l_ahwfQLdjNmNx8"
}


class PlatformAuthentication(authentication.BaseAuthentication):
    """
    Authentication based on access tokens created by Platform.

    Clients should authenticate by passing the access token in the "Authorization"
    HTTP header, prepended with the string "Bearer ". For example:

        Authorization: Bearer abc
    """
   

    def auth_required(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            authorization = request.headers.get('Authorization') or request.headers.get('authorization')
            if not authorization:
                return JsonResponse({'message': 'Unauthorized'}, status=401)

            match = re.match(r'Bearer (.+)', authorization)
            if not match:
                return JsonResponse({'message': 'Unauthorized'}, status=401)
            token = match.group(1)

            try:
                key = jwk.construct(LABS_PLATFORM_JWK)
                # Verify the token
                payload = jwt.decode(
                    token,
                    key=key,
                    algorithms=['RS256'],
                    options={'verify_exp': True},
                    leeway=60  # Clock tolerance of 1 minute
                )
                # Attach user info to the request
                request.user = {
                    'id': payload.get('sub'),
                    'name': payload.get('name'),
                    'email': payload.get('email'),
                    'pennkey': payload.get('pennkey'),
                    'pennid': payload.get('pennid'),
                    'isStaff': payload.get('is_staff'),
                    'isActive': payload.get('is_active'),
                }
                request.payload = payload
                return view_func(request, *args, **kwargs)
            except JWTError:
                return JsonResponse({'message': 'Unauthorized'}, status=401)
    return _wrapped_view

    def authenticate_header(self, request):
        return self.keyword
