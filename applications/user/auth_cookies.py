"""Helpers para emitir y limpiar cookies JWT del flujo de autenticacion.

La migracion a cookies HttpOnly requiere que login, refresh y logout compartan
exactamente los mismos atributos de cookie. Este modulo centraliza esa logica
para evitar divergencias entre endpoints durante la fase de coexistencia con el
flujo legacy basado en `Authorization: Bearer`.
"""

from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied


def _token_max_age_seconds(lifetime):
    """Convierte una vida util `timedelta` de SimpleJWT a segundos enteros."""

    return int(lifetime.total_seconds())


def _cookie_domain():
    """Obtiene el dominio configurado para cookies si existe.

    Se tolera `None` o string vacio para no obligar a declarar dominio en
    desarrollo local.
    """

    domain = getattr(settings, 'JWT_AUTH_COOKIE_DOMAIN', None)
    if domain in ('', None):
        return None
    return domain


def _build_cookie_kwargs(path, max_age):
    """Arma kwargs comunes de `set_cookie` con la politica central del backend."""

    return {
        'max_age': max_age,
        'secure': settings.JWT_AUTH_COOKIE_SECURE,
        'httponly': settings.JWT_AUTH_COOKIE_HTTP_ONLY,
        'samesite': settings.JWT_AUTH_COOKIE_SAMESITE,
        'path': path,
        'domain': _cookie_domain(),
    }


def set_auth_cookies(response, access_token, refresh_token=None):
    """Adjunta cookies de access y opcionalmente refresh a una response.

    Acepta strings o instancias de token de SimpleJWT; internamente siempre
    serializa a string para que la respuesta HTTP sea consistente.
    """

    access_value = str(access_token)
    response.set_cookie(
        settings.JWT_AUTH_COOKIE_ACCESS,
        access_value,
        **_build_cookie_kwargs(
            settings.JWT_AUTH_COOKIE_ACCESS_PATH,
            _token_max_age_seconds(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
        ),
    )

    if refresh_token is not None:
        refresh_value = str(refresh_token)
        response.set_cookie(
            settings.JWT_AUTH_COOKIE_REFRESH,
            refresh_value,
            **_build_cookie_kwargs(
                settings.JWT_AUTH_COOKIE_REFRESH_PATH,
                _token_max_age_seconds(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']),
            ),
        )

    return response


def clear_auth_cookies(response):
    """Elimina las cookies de autenticacion del backend."""

    domain = _cookie_domain()
    response.delete_cookie(
        settings.JWT_AUTH_COOKIE_ACCESS,
        path=settings.JWT_AUTH_COOKIE_ACCESS_PATH,
        domain=domain,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.JWT_AUTH_COOKIE_REFRESH,
        path=settings.JWT_AUTH_COOKIE_REFRESH_PATH,
        domain=domain,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )
    return response


def set_csrf_cookie(request, response):
    """Siembra o renueva la cookie CSRF para el frontend SPA."""

    csrf_token = get_token(request)
    response.set_cookie(
        getattr(settings, 'CSRF_COOKIE_NAME', 'csrftoken'),
        csrf_token,
        max_age=getattr(settings, 'CSRF_COOKIE_AGE', None),
        secure=settings.CSRF_COOKIE_SECURE,
        httponly=getattr(settings, 'CSRF_COOKIE_HTTPONLY', False),
        samesite=settings.CSRF_COOKIE_SAMESITE,
        path=getattr(settings, 'CSRF_COOKIE_PATH', '/'),
        domain=getattr(settings, 'CSRF_COOKIE_DOMAIN', None),
    )
    return response


def clear_csrf_cookie(response):
    """Elimina la cookie CSRF para cerrar completamente el contexto del cliente."""

    response.delete_cookie(
        getattr(settings, 'CSRF_COOKIE_NAME', 'csrftoken'),
        path=getattr(settings, 'CSRF_COOKIE_PATH', '/'),
        domain=getattr(settings, 'CSRF_COOKIE_DOMAIN', None),
        samesite=settings.CSRF_COOKIE_SAMESITE,
    )
    return response


def enforce_csrf(request):
    """Replica la verificacion CSRF de DRF para flujos autenticados por cookie."""

    check = CSRFCheck(lambda request: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise PermissionDenied(f'CSRF Failed: {reason}')


def get_access_token_from_request(request):
    """Lee el access token desde cookie cuando el cliente usa sesion HttpOnly."""

    return request.COOKIES.get(settings.JWT_AUTH_COOKIE_ACCESS)


def get_refresh_token_from_request(request):
    """Lee el refresh token desde cookie para el flujo nuevo de refresh/logout."""

    return request.COOKIES.get(settings.JWT_AUTH_COOKIE_REFRESH)
