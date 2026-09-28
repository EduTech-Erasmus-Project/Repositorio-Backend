"""Pruebas de errores recuperables en el mailer del modulo `user`.

Esta suite cubre el helper de correo de alta de usuario y deja fijo que
errores deben quedar logueados sin romper el flujo, y cuales deben seguir
propagandose por ser inesperados.
"""

from unittest.mock import patch

from django.test import SimpleTestCase

from applications.user.emailManager import SendEmailCreateUser


class UserEmailManagerErrorHandlingTests(SimpleTestCase):
    """Valida manejo seguro de errores recuperables en correos de usuario."""

    def test_send_mail_create_swallow_oserror_and_logs(self):
        """Si falla la lectura de la plantilla, el helper registra el error y no rompe."""
        with patch("builtins.open", side_effect=OSError("template missing")):
            with self.assertLogs("applications.user.emailManager", level="ERROR") as captured:
                SendEmailCreateUser().sendMailCreate("test@example.com", "Usuario")

        self.assertTrue(
            any("Error enviando correo de creacion de usuario" in message for message in captured.output)
        )

    def test_send_mail_create_does_not_swallow_unexpected_runtime_error(self):
        """Errores inesperados ya no deben quedar ocultos por un except demasiado amplio."""
        with patch("builtins.open", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                SendEmailCreateUser().sendMailCreate("test@example.com", "Usuario")
