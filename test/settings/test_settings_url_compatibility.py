"""Pruebas de contrato de rutas manuales del modulo `settings`.

Estas pruebas documentan que ciertos endpoints manuales de configuración ya no
publican variantes duplicadas con slash final. Antes coexistían ambas formas y
eso generaba colisiones de documentación y contratos ambiguos para frontend.

La suite valida el comportamiento actual: la ruta canónica sigue viva, pero el
alias retirado debe responder 404 y no ejecutar acciones de borrado o update.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.settings.models import (
    EmailExtensionsTeacher,
    OptionRegisterEmailExtension,
    UserTypeWithOption,
)
from applications.user.models import Administrator


class SettingsURLCompatibilityTests(TestCase):
    """Asegura que los aliases retirados en `settings` no vuelvan a resolverse."""

    def setUp(self):
        """Prepara un administrador autenticado y el catálogo mínimo del módulo.

        Se crean dominios y opciones reales para poder distinguir un 404 de
        contrato de ruta frente a un 404 por recurso inexistente.
        """
        self.client = APIClient()
        self.user_model = get_user_model()
        self.admin_user = self._create_admin_user()
        self.client.force_authenticate(user=self.admin_user)

        self.option_all = OptionRegisterEmailExtension.objects.create(type_option="ALL")
        self.option_only = OptionRegisterEmailExtension.objects.create(type_option="ONLY")
        self.domain = EmailExtensionsTeacher.objects.create(
            domain="compat.ups.edu.ec",
            is_active=True,
            option_register_email=self.option_all,
        )
        self.user_type = UserTypeWithOption.objects.create(
            description="Teacher register compatibility",
            option_register=self.option_all,
        )

    def _create_admin_user(self):
        """Construye un usuario administrador capaz de consumir endpoints protegidos."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin settings urls",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email="settings-url-admin@example.com",
            first_name="Settings",
            last_name="URLs",
            password="StrongPass123",
        )
        user.administrator = administrator
        user.save()
        return user

    def test_email_domain_active_rejects_trailing_slash(self):
        """El listado manual de dominios activos ya no acepta slash final."""
        response = self.client.get("/api/v1/settings/email-domain/active/")
        self.assertEqual(response.status_code, 404)

    def test_email_domain_delete_rejects_trailing_slash(self):
        """El delete legacy con slash debe fallar y no borrar el dominio.

        Además del status, se valida que la fila permanezca en base para dejar
        claro que no hubo side effects.
        """
        response = self.client.delete(
            f"/api/v1/settings/email-domain/{self.domain.id}/?type=TEACHER"
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(EmailExtensionsTeacher.objects.filter(pk=self.domain.id).exists())

    def test_email_domain_update_rejects_trailing_slash(self):
        """La ruta manual de update con slash también quedó fuera del contrato."""
        response = self.client.put(
            f"/api/v1/settings/email-domain-update/{self.domain.id}/?type=TEACHER",
            {"domain": "compat-update.ups.edu.ec"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_user_type_option_update_rejects_trailing_slash(self):
        """El alias retirado de actualización de opción de registro debe dar 404."""
        response = self.client.put(
            f"/api/v1/settings/type-user-option-register-update/{self.user_type.id}/",
            {"option_register": self.option_only.id},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
