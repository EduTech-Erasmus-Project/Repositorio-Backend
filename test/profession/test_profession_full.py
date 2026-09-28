"""Pruebas funcionales del módulo `profession`.

Esta suite cubre el catálogo de profesiones usado por el perfil docente. El
archivo valida:
- que listado y detalle sigan siendo públicos
- que solo admin y superuser puedan mutar el catalogo
- que create y update apliquen las validaciones básicas esperadas
- que los cambios realmente se persistan o eliminen en la base
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.profession.models import Profession
from applications.user.models import Administrator, Teacher


class ProfessionFullFlowTests(TestCase):
    """Verifica permisos, validaciones y persistencia del catálogo de profesiones."""

    def setUp(self):
        """Crea profesiones base y clientes autenticados para comparar permisos.

        La fixture prepara cuatro perspectivas de acceso: admin, superuser,
        teacher y anónimo. Con eso cada prueba puede mostrar quien solo lee el
        catalogo y quien realmente puede administrarlo.
        """
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.profession_1 = Profession.objects.create(description="Ingeniero")
        self.profession_2 = Profession.objects.create(description="Docente")

        self.admin_client = self._build_authenticated_client(self._create_admin_user())
        self.superuser_client = self._build_authenticated_client(self._create_superuser_user())
        self.teacher_client = self._build_authenticated_client(self._create_teacher_user())
        self.anonymous_client = APIClient()

    def _next_email(self, prefix):
        """Genera correos únicos para evitar conflictos entre pruebas."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _build_authenticated_client(self, user):
        """Autentica por JWT y devuelve un cliente listo para endpoints protegidos."""
        client = APIClient()
        login_response = client.post(
            "/api/v1/login/",
            {"email": user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        return client

    def _create_admin_user(self):
        """Crea administrador activo."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin Profession",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin"),
            first_name="Admin",
            last_name="Profession",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_superuser_user(self):
        """Crea superusuario para validar permisos equivalentes a admin."""
        return self.user_model.objects.create_superuser(
            email=self._next_email("superuser"),
            first_name="Super",
            last_name="Profession",
            password=self.password,
        )

    def _create_teacher_user(self):
        """Crea docente para validar denegación en endpoints administrativos."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher"),
            first_name="Teacher",
            last_name="Profession",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def test_list_and_retrieve_are_public(self):
        """Listado y detalle deben seguir accesibles sin autenticación."""
        list_response = self.anonymous_client.get("/api/v1/profession/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 2)

        retrieve_response = self.anonymous_client.get(f"/api/v1/profession/{self.profession_1.id}/")
        self.assertEqual(retrieve_response.status_code, 200, retrieve_response.data)
        self.assertEqual(retrieve_response.data["id"], self.profession_1.id)
        self.assertEqual(retrieve_response.data["description"], "Ingeniero")

    def test_create_requires_admin_permissions(self):
        """Solo admin y superuser pueden crear nuevas profesiones."""
        payload = {"description": "Arquitecto"}

        anonymous_response = self.anonymous_client.post(
            "/api/v1/profession/",
            payload,
            format="json",
        )
        self.assertEqual(anonymous_response.status_code, 401)

        teacher_response = self.teacher_client.post(
            "/api/v1/profession/",
            payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/profession/",
            payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.data)

        super_response = self.superuser_client.post(
            "/api/v1/profession/",
            {"description": "Médico"},
            format="json",
        )
        self.assertEqual(super_response.status_code, 200, super_response.data)

    def test_create_validates_required_and_unique(self):
        """Valida requeridos y unicidad para evitar profesiones vacías o duplicadas."""
        missing_required = self.admin_client.post(
            "/api/v1/profession/",
            {},
            format="json",
        )
        self.assertEqual(missing_required.status_code, 400)
        self.assertIn("description", missing_required.data)

        duplicate = self.admin_client.post(
            "/api/v1/profession/",
            {"description": "Ingeniero"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("description", duplicate.data)

    def test_update_requires_admin_and_persists_changes(self):
        """El update es administrativo y debe dejar el cambio persistido en la base."""
        teacher_response = self.teacher_client.put(
            f"/api/v1/profession/{self.profession_1.id}/",
            {"description": "Ingeniero Senior"},
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.put(
            f"/api/v1/profession/{self.profession_1.id}/",
            {"description": "Ingeniero Senior"},
            format="json",
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.data)
        self.profession_1.refresh_from_db()
        self.assertEqual(self.profession_1.description, "Ingeniero Senior")

    def test_update_validates_required_field(self):
        """El update completo exige `description` y debe rechazar payload vacío."""
        invalid_update = self.admin_client.put(
            f"/api/v1/profession/{self.profession_1.id}/",
            {},
            format="json",
        )
        self.assertEqual(invalid_update.status_code, 400)
        self.assertIn("description", invalid_update.data)

    def test_delete_requires_admin_permissions(self):
        """El delete solo admite admin o superuser y debe borrar el registro."""
        teacher_delete = self.teacher_client.delete(f"/api/v1/profession/{self.profession_2.id}/")
        self.assertEqual(teacher_delete.status_code, 403)

        admin_delete = self.admin_client.delete(f"/api/v1/profession/{self.profession_2.id}/")
        self.assertEqual(admin_delete.status_code, 200, admin_delete.data)
        self.assertFalse(Profession.objects.filter(id=self.profession_2.id).exists())
