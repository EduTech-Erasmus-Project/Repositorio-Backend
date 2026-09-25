"""Pruebas de helpers y autenticacion por token del módulo `user`.

La suite cubre la lógica heredada de expiración de tokens DRF y la clase
`ExpiringTokenAuthentication`, dejando claro que pasa con tokens válidos,
inválidos y expirados.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from applications.user.authentication import (
    ExpiringTokenAuthentication,
    expires_in,
    is_token_expired,
    token_expire_handler,
)


class TokenAuthenticationHelpersTests(TestCase):
    """Valida helpers de expiración y rotación de tokens DRF."""

    def setUp(self):
        """Crea un usuario base para emitir tokens en las pruebas."""
        self.user = get_user_model().objects.create_user(
            email="auth-tests@example.com",
            first_name="Auth",
            last_name="Tests",
            password="SafePassword123",
        )

    def test_expires_in_returns_positive_delta_for_fresh_token(self):
        """Comprueba que un token nuevo aún tiene tiempo de vida disponible."""
        token = Token.objects.create(user=self.user)

        left_time = expires_in(token)

        self.assertGreater(left_time.total_seconds(), 0)

    def test_is_token_expired_returns_true_for_expired_token(self):
        """Confirma que se detecta un token vencido por fecha de creación."""
        token = Token.objects.create(user=self.user)
        token.created = timezone.now() - timedelta(
            seconds=settings.TOKEN_EXPIRED_AFTER_SECONDS + 1
        )
        token.save(update_fields=["created"])

        self.assertTrue(is_token_expired(token))

    def test_token_expire_handler_rotates_expired_token(self):
        """Valida rotación de clave cuando el token ya expiró."""
        token = Token.objects.create(user=self.user)
        old_key = token.key
        token.created = timezone.now() - timedelta(
            seconds=settings.TOKEN_EXPIRED_AFTER_SECONDS + 1
        )
        token.save(update_fields=["created"])

        is_expired, new_token = token_expire_handler(token)

        self.assertTrue(is_expired)
        self.assertNotEqual(old_key, new_token.key)
        self.assertFalse(Token.objects.filter(key=old_key).exists())


class ExpiringTokenAuthenticationTests(TestCase):
    """Cubre autenticación con token valido, invalido y expirado."""

    def setUp(self):
        """Prepara usuario de prueba e instancia del autenticador custom."""
        self.user = get_user_model().objects.create_user(
            email="auth-class-tests@example.com",
            first_name="AuthClass",
            last_name="Tests",
            password="SafePassword123",
        )
        self.authenticator = ExpiringTokenAuthentication()

    def test_authenticate_credentials_rejects_invalid_token(self):
        """Rechaza credenciales cuando la clave del token no existe."""
        with self.assertRaises(AuthenticationFailed):
            self.authenticator.authenticate_credentials("invalid-token")

    def test_authenticate_credentials_returns_user_and_token_when_valid(self):
        """Retorna usuario y token cuando la clave es válida y vigente."""
        token = Token.objects.create(user=self.user)

        authenticated_user, authenticated_token = self.authenticator.authenticate_credentials(
            token.key
        )

        self.assertEqual(authenticated_user.id, self.user.id)
        self.assertEqual(authenticated_token.key, token.key)

    def test_authenticate_credentials_raises_for_expired_token(self):
        """Lanza error de autenticación para tokens fuera de vigencia."""
        token = Token.objects.create(user=self.user)
        token.created = timezone.now() - timedelta(
            seconds=settings.TOKEN_EXPIRED_AFTER_SECONDS + 1
        )
        token.save(update_fields=["created"])

        with self.assertRaises(AuthenticationFailed):
            self.authenticator.authenticate_credentials(token.key)
