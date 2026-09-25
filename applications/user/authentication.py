"""Autenticación heredada basada en tokens con expiración.

Aunque el proyecto hoy usa JWT en varios flujos, este módulo conserva la
estrategia de `TokenAuthentication` expirable para endpoints o integraciones que
siguen dependiendo de DRF authtoken. La lógica central calcula el tiempo de
vida restante del token y obliga a reautenticarse cuando ya expiro.
"""

from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from applications.user.auth_cookies import enforce_csrf

from datetime import timedelta
from django.utils import timezone
from django.conf import settings


def expires_in(token):
    """Devuelve el tiempo restante antes de que expire un token DRF."""

    time_elapsed = timezone.now() - token.created
    left_time = timedelta(seconds = settings.TOKEN_EXPIRED_AFTER_SECONDS) - time_elapsed
    return left_time


def is_token_expired(token):
    """Indica si el token ya supero la ventana de vigencia configurada."""

    return expires_in(token) < timedelta(seconds = 0)


def token_expire_handler(token):
    """Renueva el token expirado recreando la fila asociada al usuario.

    El método devuelve una tupla `(is_expired, token)` para que la capa de
    autenticación pueda decidir si rechaza la credencial actual o sigue con el
    token vigente.
    """

    is_expired = is_token_expired(token)
    if is_expired:
        token.delete()
        token = Token.objects.create(user = token.user)
    return is_expired, token


class ExpiringTokenAuthentication(TokenAuthentication):
    """Extiende `TokenAuthentication` con verificación de expiración.

    Si el token existe pero ya expiró, se elimina y se recrea para dejar el
    sistema en un estado consistente, pero se rechaza la credencial actual para
    forzar un nuevo login del cliente.
    """

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key = key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid Token")
        
        if not token.user.is_active:
            raise AuthenticationFailed("User is not active")

        is_expired, token = token_expire_handler(token)
        if is_expired:
            raise AuthenticationFailed("The Token is expired")
        
        return (token.user, token)


class CookieJWTAuthentication(JWTAuthentication):
    """Acepta JWT por header Bearer o por cookie HttpOnly.

    Se prioriza el header `Authorization` para conservar compatibilidad con el
    frontend actual. Si el header no existe, intenta autenticar usando la
    cookie configurada en `settings.JWT_AUTH_COOKIE_ACCESS`.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE_ACCESS)
        if raw_token is None:
            return None

        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            enforce_csrf(request)

        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])

        return self.get_user(validated_token), validated_token
