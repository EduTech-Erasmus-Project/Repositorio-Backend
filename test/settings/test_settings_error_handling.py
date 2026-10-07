"""Pruebas de manejo de errores del módulo `settings`.

Esta suite cubre los caminos donde la configuración SMTP o el mailer pueden
fallar. El objetivo es dejar documentado que errores se manejan de forma
controlada, cuales siguen propagándose y que mensajes legacy conserva hoy el
endpoint.
"""

import smtplib
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.settings.models import Email
from applications.user.models import Administrator


class SettingsErrorHandlingTests(TestCase):
    """Verifica errores controlados y errores inesperados en la configuración SMTP."""

    def setUp(self):
        """Autentica un administrador para probar endpoints operativos protegidos."""
        self.client = APIClient()
        self.user_model = get_user_model()
        self.admin_user = self._create_admin_user()
        self.client.force_authenticate(user=self.admin_user)

    def _create_admin_user(self):
        """Construye un administrador activo para las pruebas del módulo."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin settings errors",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email="settings-errors-admin@example.com",
            first_name="Settings",
            last_name="Errors",
            password="StrongPass123",
        )
        user.administrator = administrator
        user.save()
        return user

    def test_email_get_without_config_returns_legacy_message(self):
        """Si no hay configuración SMTP, el endpoint responde sin explotar."""
        response = self.client.get("/api/v1/settings/email/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], 204)
        self.assertEqual(
            response.data["message"],
            "The company don't have an assigned email",
        )

    def test_email_post_without_config_returns_controlled_error(self):
        """Si no existe registro base de correo, el update falla de forma controlada."""
        payload = {
            "host": "smtp.example.com",
            "username": "admin@example.com",
            "password": "new-pass",
            "port": "587",
            "tls": True,
            "email_from": "admin@example.com",
        }

        response = self.client.post("/api/v1/settings/email/", payload, format="json")

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(
            response.data["message"],
            "The company don't have an assigned email",
        )

    def test_email_post_updates_existing_config(self):
        """Mantiene el flujo valido de actualización de configuración SMTP."""
        email = Email(host="smtp.old.local", username="old@example.com", port="587", tls=True, email_from="old@example.com")
        email.password = email.encrypt_password("old-pass").decode("utf-8")
        email.save()

        payload = {
            "host": "smtp.new.local",
            "username": "new@example.com",
            "password": "new-pass",
            "port": "2525",
            "tls": False,
            "email_from": "new@example.com",
        }

        response = self.client.post("/api/v1/settings/email/", payload, format="json")

        email.refresh_from_db()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(email.host, "smtp.new.local")
        self.assertEqual(email.username, "new@example.com")
        self.assertEqual(email.port, "2525")
        self.assertFalse(email.tls)
        self.assertEqual(email.email_from, "new@example.com")
        self.assertEqual(email.decrypt_password(), "new-pass")

    def test_email_testing_rejects_invalid_payload(self):
        """El endpoint de prueba SMTP valida el destinatario requerido."""
        response = self.client.post(
            "/api/v1/settings/email-testing/",
            {"host": "smtp.local"},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["message"], "Validation error")
        self.assertIn("emailtest", response.data["errors"])

    def test_email_testing_returns_400_for_expected_smtp_error(self):
        """Errores SMTP esperables deben responder 400 sin romper el endpoint."""
        payload = {"emailtest": "destino@example.com"}

        with patch(
            "applications.settings.views.mail_aproved.sendEmailTesting",
            side_effect=smtplib.SMTPException("smtp failed"),
        ):
            response = self.client.post(
                "/api/v1/settings/email-testing/",
                payload,
                format="json",
            )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["message"], "smtp failed")

    def test_email_testing_does_not_swallow_unexpected_runtime_error(self):
        """Un RuntimeError inesperado ya no debe quedar oculto por un except genérico."""
        payload = {"emailtest": "destino@example.com"}

        with patch(
            "applications.settings.views.mail_aproved.sendEmailTesting",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    "/api/v1/settings/email-testing/",
                    payload,
                    format="json",
                )
