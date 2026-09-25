"""Pruebas de compatibilidad con variables de entorno legacy en `user`.

Estas pruebas documentan fallbacks usados por flujos de correo y recuperación
de password cuando no existe la variable nueva pero si la variable histórica.
"""

import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class UserEnvCompatibilityTests(TestCase):
    """Compatibilidad de variables de entorno legacy en endpoints del módulo user."""

    def setUp(self):
        """Prepara cliente API y modelo de usuario para probar el flujo de reset."""
        self.client = APIClient()
        self.user_model = get_user_model()

    @patch("applications.user.views.mail.sendMailTest")
    def test_request_password_reset_uses_domain_host_when_domain_host_roa_is_missing(
        self,
        mock_send_mail,
    ):
        """Si falta DOMAIN_HOST_ROA, el reset debe caer a DOMAIN_HOST sin romper."""
        user = self.user_model.objects.create_general_user(
            email="reset-env@example.com",
            first_name="Reset",
            last_name="Env",
            password="StrongPass123",
        )

        with patch.dict(os.environ, {"DOMAIN_HOST": "http://fallback.local"}, clear=False):
            os.environ.pop("DOMAIN_HOST_ROA", None)

            response = self.client.post(
                "/api/v1/request-reset-email/",
                {"email": user.email},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        mock_send_mail.assert_called_once()
        _, reset_url, _ = mock_send_mail.call_args[0]
        self.assertTrue(reset_url.startswith("http://fallback.local"))
