"""Pruebas de validación de payloads en el módulo `settings`.

Esta suite cubre validaciones de serializers y query params en endpoints de
dominios de correo y opciones de registro. La idea es dejar claro que errores
se rechazan antes de tocar la base y cuales flujos validos deben seguir
funcionando.
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


class SettingsValidationSerializersTests(TestCase):
    """Verifica validaciones de entrada en dominios de correo y opciones de registro."""

    def setUp(self):
        """Crea un admin autenticado y el catálogo mínimo para probar validaciones."""
        self.client = APIClient()
        self.user_model = get_user_model()
        self.admin_user = self._create_admin_user()
        self.client.force_authenticate(user=self.admin_user)
        self.option_all = OptionRegisterEmailExtension.objects.create(type_option="ALL")
        self.option_only = OptionRegisterEmailExtension.objects.create(type_option="ONLY")
        self.user_type = UserTypeWithOption.objects.create(
            description="Teacher register",
            option_register=self.option_all,
        )

    def _create_admin_user(self):
        """Crea un administrador activo para consumir endpoints protegidos."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin settings",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email="settings-admin@example.com",
            first_name="Settings",
            last_name="Admin",
            password="StrongPass123",
        )
        user.administrator = administrator
        user.save()
        return user

    def test_email_domain_create_rejects_invalid_type(self):
        """Rechaza tipos no soportados antes de intentar crear dominios."""
        payload = {
            "type": "INVALID",
            "domain": "ups.edu.ec",
            "is_active": True,
            "option_register_email": self.option_all.id,
        }

        response = self.client.post("/api/v1/settings/email-domain/", payload, format="json")

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["message"], "Create error")
        self.assertIn("type", response.data["errors"])
        self.assertFalse(EmailExtensionsTeacher.objects.exists())

    def test_email_domain_create_keeps_valid_teacher_flow(self):
        """Mantiene el alta valida de dominios para docentes."""
        payload = {
            "type": "TEACHER",
            "domain": "teacher.ups.edu.ec",
            "is_active": True,
            "option_register_email": self.option_all.id,
        }

        response = self.client.post("/api/v1/settings/email-domain/", payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Create Successful")
        self.assertTrue(
            EmailExtensionsTeacher.objects.filter(domain="teacher.ups.edu.ec").exists()
        )

    def test_email_domain_list_rejects_invalid_option_type(self):
        """Valida que el parámetro option tenga formato númerico cuando se envía."""
        response = self.client.get(
            "/api/v1/settings/email-domain/?type=TEACHER&option=abc"
        )

        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(response.data["message"], "List error")
        self.assertIn("option", response.data["errors"])

    def test_email_domain_update_rejects_invalid_type(self):
        """Evita entrar al update si el tipo de dominio no es válido."""
        domain = EmailExtensionsTeacher.objects.create(
            domain="old.ups.edu.ec",
            is_active=True,
            option_register_email=self.option_all,
        )

        response = self.client.put(
            f"/api/v1/settings/email-domain-update/{domain.id}?type=INVALID",
            {"domain": "new.ups.edu.ec"},
            format="json",
        )

        domain.refresh_from_db()
        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(response.data["message"], "Update error")
        self.assertIn("type", response.data["errors"])
        self.assertEqual(domain.domain, "old.ups.edu.ec")

    def test_user_type_option_update_rejects_unknown_option_register(self):
        """Valida la FK antes de intentar guardar la relación de tipos."""
        response = self.client.put(
            f"/api/v1/settings/type-user-option-register-update/{self.user_type.id}",
            {"option_register": 999999},
            format="json",
        )

        self.user_type.refresh_from_db()
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["message"], "Error Update")
        self.assertIn("option_register", response.data["errors"])
        self.assertEqual(self.user_type.option_register_id, self.option_all.id)

    def test_user_type_option_update_keeps_valid_flow(self):
        """Permite actualizar la opción de registro cuando el dato es válido."""
        response = self.client.put(
            f"/api/v1/settings/type-user-option-register-update/{self.user_type.id}",
            {"option_register": self.option_only.id},
            format="json",
        )

        self.user_type.refresh_from_db()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Update Successful")
        self.assertEqual(self.user_type.option_register_id, self.option_only.id)
