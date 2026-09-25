"""Pruebas funcionales del módulo `license`.

Esta suite cubre el catálogo de licencias que el sistema expone como CRUD
administrativo y también como fuente de datos localizada para filtros del
frontend. El archivo valida:
- localización del listado según `Accept-Language`
- permisos por rol para crear, actualizar y eliminar
- validaciones básicas de requeridos y unicidad
- comportamiento del endpoint manual `endpoint-filter`
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.license.models import License
from applications.user.models import Administrator, Teacher


class LicenseFullFlowTests(TestCase):
    """Verifica localización, permisos y persistencia del catálogo de licencias."""

    def setUp(self):
        """Crea licencias base y clientes autenticados para comparar permisos.

        La fixture prepara cuatro perspectivas de acceso: admin, superuser,
        teacher y anónimo. Así cada prueba deja claro quién puede leer o
        mutar cada endpoint del módulo.
        """
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.license_1 = License.objects.create(
            name_es="Creative Commons",
            name_en="Creative Commons",
            value="CC",
        )
        self.license_2 = License.objects.create(
            name_es="Dominio Público",
            name_en="Public Domain",
            value="PD",
        )

        self.admin_client = self._build_authenticated_client(self._create_admin_user())
        self.superuser_client = self._build_authenticated_client(self._create_superuser_user())
        self.teacher_client = self._build_authenticated_client(self._create_teacher_user())
        self.anonymous_client = APIClient()

    def _next_email(self, prefix):
        """Genera correos únicos para evitar colisiones entre pruebas."""
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
            observation="Admin License",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin"),
            first_name="Admin",
            last_name="License",
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
            last_name="License",
            password=self.password,
        )

    def _create_teacher_user(self):
        """Crea docente para validar denegación en endpoints administrativos."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher"),
            first_name="Teacher",
            last_name="License",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def test_list_without_accept_language_header_returns_message(self):
        """Sin `Accept-Language` el listado no se localiza y devuelve un mensaje guía."""
        response = self.anonymous_client.get("/api/v1/license/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Accept Language in header is required")

    def test_list_in_spanish_returns_localized_values(self):
        """Con `Accept-Language=es` devuelve nombres y etiqueta principal en español."""
        response = self.anonymous_client.get(
            "/api/v1/license/",
            HTTP_ACCEPT_LANGUAGE="es",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["key"], "license")
        self.assertEqual(response.data["filter_param_value"], "value")
        self.assertEqual(response.data["name"], "Licencia")
        values_by_id = {value["id"]: value for value in response.data["values"]}
        self.assertEqual(values_by_id[self.license_1.id]["name"], "Creative Commons")
        self.assertEqual(values_by_id[self.license_2.id]["name"], "Dominio Público")

    def test_list_in_english_returns_localized_values(self):
        """Con `Accept-Language=en` devuelve nombres y etiqueta principal en inglés."""
        response = self.anonymous_client.get(
            "/api/v1/license/",
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["key"], "license")
        self.assertEqual(response.data["filter_param_value"], "value")
        self.assertEqual(response.data["name"], "License")
        values_by_id = {value["id"]: value for value in response.data["values"]}
        self.assertEqual(values_by_id[self.license_1.id]["name"], "Creative Commons")
        self.assertEqual(values_by_id[self.license_2.id]["name"], "Public Domain")

    def test_list_with_unsupported_language_returns_406(self):
        """Con idioma no soportado responde 406 para dejar explicito el error."""
        response = self.anonymous_client.get(
            "/api/v1/license/",
            HTTP_ACCEPT_LANGUAGE="fr",
        )
        self.assertEqual(response.status_code, 406, response.data)
        self.assertIn("message", response.data)

    def test_retrieve_is_public(self):
        """El detalle de una licencia individual debe seguir siendo público."""
        response = self.anonymous_client.get(f"/api/v1/license/{self.license_1.id}/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], self.license_1.id)
        self.assertEqual(response.data["name"], "Creative Commons")
        self.assertEqual(response.data["value"], "CC")

    def test_create_requires_admin_permissions(self):
        """Solo admin y superuser pueden crear nuevas licencias del catálogo."""
        payload = {"name_es": "GPL", "name_en": "GPL", "value": "GPL"}

        anonymous_response = self.anonymous_client.post(
            "/api/v1/license/",
            payload,
            format="json",
        )
        self.assertEqual(anonymous_response.status_code, 401)

        teacher_response = self.teacher_client.post(
            "/api/v1/license/",
            payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/license/",
            payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 201, admin_response.data)

        super_response = self.superuser_client.post(
            "/api/v1/license/",
            {"name_es": "MIT", "name_en": "MIT", "value": "MIT"},
            format="json",
        )
        self.assertEqual(super_response.status_code, 201, super_response.data)

    def test_create_validates_required_and_unique_fields(self):
        """Valida requeridos y unicidad para evitar licencias duplicadas o incompletas."""
        missing_required = self.admin_client.post(
            "/api/v1/license/",
            {"name_es": "Solo Español"},
            format="json",
        )
        self.assertEqual(missing_required.status_code, 400)
        self.assertIn("name_en", missing_required.data)
        self.assertIn("value", missing_required.data)

        duplicate = self.admin_client.post(
            "/api/v1/license/",
            {"name_es": "Creative Commons", "name_en": "Creative Commons", "value": "CC"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertTrue(
            "name_es" in duplicate.data or "name_en" in duplicate.data or "value" in duplicate.data
        )

    def test_update_and_partial_update_require_admin_and_persist(self):
        """PUT y PATCH son administrativos y deben persistir cambios en la base."""
        teacher_put = self.teacher_client.put(
            f"/api/v1/license/{self.license_1.id}/",
            {"name_es": "CC BY", "name_en": "CC BY", "value": "CC-BY"},
            format="json",
        )
        self.assertEqual(teacher_put.status_code, 403)

        admin_put = self.admin_client.put(
            f"/api/v1/license/{self.license_1.id}/",
            {"name_es": "CC BY", "name_en": "CC BY", "value": "CC-BY"},
            format="json",
        )
        self.assertEqual(admin_put.status_code, 200, admin_put.data)
        self.license_1.refresh_from_db()
        self.assertEqual(self.license_1.name_es, "CC BY")
        self.assertEqual(self.license_1.value, "CC-BY")

        teacher_patch = self.teacher_client.patch(
            f"/api/v1/license/{self.license_1.id}/",
            {"value": "CC-BY-SA"},
            format="json",
        )
        self.assertEqual(teacher_patch.status_code, 403)

        admin_patch = self.admin_client.patch(
            f"/api/v1/license/{self.license_1.id}/",
            {"value": "CC-BY-SA"},
            format="json",
        )
        self.assertEqual(admin_patch.status_code, 200, admin_patch.data)
        self.license_1.refresh_from_db()
        self.assertEqual(self.license_1.value, "CC-BY-SA")

    def test_delete_requires_admin_permissions(self):
        """DELETE solo admite admin o superuser y debe borrar el registro."""
        teacher_delete = self.teacher_client.delete(f"/api/v1/license/{self.license_2.id}/")
        self.assertEqual(teacher_delete.status_code, 403)

        admin_delete = self.admin_client.delete(f"/api/v1/license/{self.license_2.id}/")
        self.assertEqual(admin_delete.status_code, 200)
        self.assertFalse(License.objects.filter(id=self.license_2.id).exists())

    def test_endpoint_filter_supports_language_header(self):
        """`endpoint-filter` también se localiza y exige header de idioma para responder."""
        missing_header = self.anonymous_client.get("/api/v1/endpoint-filter")
        self.assertEqual(missing_header.status_code, 200, missing_header.data)
        self.assertEqual(missing_header.data["message"], "Accept Language in header is required")

        response_es = self.anonymous_client.get(
            "/api/v1/endpoint-filter",
            HTTP_ACCEPT_LANGUAGE="es",
        )
        self.assertEqual(response_es.status_code, 200, response_es.data)
        self.assertEqual(len(response_es.data), 3)
        self.assertEqual(response_es.data[0]["endpoint"], "https://repositorio.edutech-project.org/api/v1/license")

        response_en = self.anonymous_client.get(
            "/api/v1/endpoint-filter",
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response_en.status_code, 200, response_en.data)
        self.assertEqual(len(response_en.data), 3)
        self.assertEqual(response_en.data[0]["name"], "License")
