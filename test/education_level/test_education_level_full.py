"""Pruebas completas del catálogo `education_level`.

Esta suite verifica tres aspectos del módulo:
- cómo responde el listado según `Accept-Language`
- que operaciones son públicas y cuales quedan reservadas a admin/superuser
- que el CRUD respeta validaciones básicas como campos requeridos y unicidad

El objetivo es que cualquier cambio en vistas, permisos o serializers del
catalogo rompa una prueba si altera el comportamiento esperado.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.user.models import Administrator, Teacher


class EducationLevelFullFlowTests(TestCase):
    """Cubre localización, permisos y CRUD del catálogo de niveles educativos."""

    def setUp(self):
        """Prepara el catálogo base y clientes autenticados por rol.

        La fixture crea dos education levels existentes y tres clientes útiles
        para comparar permisos:
        - administrador
        - superusuario
        - docente sin privilegios administrativos

        también deja un cliente anónimo para los endpoints públicos.
        """
        self.user_model = get_user_model()
        self._sequence = 0
        self.password = "StrongPass123"

        self.level_1 = EducationLevel.objects.create(name_es="Primaria", name_en="Primary")
        self.level_2 = EducationLevel.objects.create(name_es="Secundaria", name_en="Secondary")

        self.admin_client = self._build_authenticated_client(self._create_admin_user())
        self.superuser_client = self._build_authenticated_client(self._create_superuser_user())
        self.teacher_client = self._build_authenticated_client(self._create_teacher_user())
        self.anonymous_client = APIClient()

    def _next_email(self, prefix):
        """Genera correos únicos para evitar colisiones entre casos de prueba."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _build_authenticated_client(self, user):
        """Autentica un cliente vía JWT para simular requests reales."""
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
        """Crea un usuario administrador activo para operaciones permitidas."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin EducationLevel",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin"),
            first_name="Admin",
            last_name="EducationLevel",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_superuser_user(self):
        """Crea un superusuario para validar permisos equivalentes a admin."""
        return self.user_model.objects.create_superuser(
            email=self._next_email("superuser"),
            first_name="Super",
            last_name="EducationLevel",
            password=self.password,
        )

    def _create_teacher_user(self):
        """Crea un docente para comprobar accesos denegados en endpoints admin."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher"),
            first_name="Teacher",
            last_name="EducationLevel",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def test_list_without_accept_language_header_returns_message(self):
        """Verifica el mensaje explicito cuando falta `Accept-Language`.

        Esta prueba protege el comportamiento heredado del endpoint: en vez de
        devolver 400, responde 200 con un mensaje que indica que el header es
        obligatorio para construir la salida localizada.
        """
        response = self.anonymous_client.get("/api/v1/education-level/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Accept Language in header is required")

    def test_list_in_spanish_returns_localized_values(self):        
        """Comprueba la salida en español del listado público.

        Valida tanto el wrapper de filtros (`key`, `name`, `filter_param_value`)
        como el nombre localizado de los niveles dentro de `values`.
        """

        response = self.anonymous_client.get(
            "/api/v1/education-level/",
            HTTP_ACCEPT_LANGUAGE="es",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["key"], "education_levels")
        self.assertEqual(response.data["name"], "Nivel de educación")
        self.assertEqual(response.data["filter_param_value"], "id")
        self.assertEqual(response.data["values"][0]["id"], self.level_1.id)
        self.assertEqual(response.data["values"][0]["name"], "Primaria")

    def test_list_in_english_returns_localized_values(self):
        """Comprueba la salida en inglés del mismo listado público."""
        response = self.anonymous_client.get(
            "/api/v1/education-level/",
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["key"], "education_levels")
        self.assertEqual(response.data["name"], "Education Level")
        self.assertEqual(response.data["filter_param_value"], "id")
        self.assertEqual(response.data["values"][0]["id"], self.level_1.id)
        self.assertEqual(response.data["values"][0]["name"], "Primary")

    def test_list_with_unsupported_language_returns_406(self):
        """Valida el rechazo de idiomas no soportados por la vista."""
        response = self.anonymous_client.get(
            "/api/v1/education-level/",
            HTTP_ACCEPT_LANGUAGE="fr",
        )
        self.assertEqual(response.status_code, 406, response.data)
        self.assertIn("message", response.data)

    def test_retrieve_is_public(self):
        """Asegura que el detalle por id siga siendo público."""
        response = self.anonymous_client.get(f"/api/v1/education-level/{self.level_1.id}/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], self.level_1.id)
        self.assertEqual(response.data["name_es"], "Primaria")

    def test_create_requires_admin_permissions(self):
        """Verifica que solo admin y superuser puedan crear registros nuevos.

        El caso compara tres escenarios en la misma prueba:
        - anónimo: debe recibir 401
        - docente: debe recibir 403
        - admin/superuser: deben poder crear correctamente
        """
        payload = {"name_es": "Inicial", "name_en": "Initial"}

        anonymous_response = self.anonymous_client.post(
            "/api/v1/education-level/",
            payload,
            format="json",
        )
        self.assertEqual(anonymous_response.status_code, 401)

        teacher_response = self.teacher_client.post(
            "/api/v1/education-level/",
            payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/education-level/",
            payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 201, admin_response.data)

        super_response = self.superuser_client.post(
            "/api/v1/education-level/",
            {"name_es": "Bachillerato", "name_en": "High School"},
            format="json",
        )
        self.assertEqual(super_response.status_code, 201, super_response.data)

    def test_create_validates_required_and_unique_fields(self):
        """Comprueba validaciones básicas del serializer de creación.

        Este caso protege dos reglas importantes del catálogo:
        - `name_en` es obligatorio
        - `name_es` y `name_en` no deben duplicar registros existentes
        """
        missing_field_response = self.admin_client.post(
            "/api/v1/education-level/",
            {"name_es": "Solo Español"},
            format="json",
        )
        self.assertEqual(missing_field_response.status_code, 400)
        self.assertIn("name_en", missing_field_response.data)

        duplicate_response = self.admin_client.post(
            "/api/v1/education-level/",
            {"name_es": "Primaria", "name_en": "Primary"},
            format="json",
        )
        self.assertEqual(duplicate_response.status_code, 400)
        self.assertTrue("name_es" in duplicate_response.data or "name_en" in duplicate_response.data)

    def test_update_requires_admin_and_persists_changes(self):
        """Comprueba que update requiere permisos altos y si persiste cambios.

        Primero valida que un docente no puede actualizar. Luego confirma que
        un administrador si puede modificar ambos nombres y que el cambio queda
        realmente guardado en base de datos.
        """
        teacher_response = self.teacher_client.put(
            f"/api/v1/education-level/{self.level_1.id}/",
            {"name_es": "Primaria X", "name_en": "Primary X"},
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.put(
            f"/api/v1/education-level/{self.level_1.id}/",
            {"name_es": "Primaria Actualizada", "name_en": "Primary Updated"},
            format="json",
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.data)
        self.level_1.refresh_from_db()
        self.assertEqual(self.level_1.name_es, "Primaria Actualizada")
        self.assertEqual(self.level_1.name_en, "Primary Updated")

    def test_delete_requires_admin_and_removes_record(self):
        """Comprueba que delete es administrativo y borra el registro.

        Igual que en update, se valida primero el rechazo para docente y luego
        la eliminación efectiva cuando la operación la ejecuta un admin.
        """
        teacher_response = self.teacher_client.delete(f"/api/v1/education-level/{self.level_2.id}/")
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.delete(f"/api/v1/education-level/{self.level_2.id}/")
        self.assertEqual(admin_response.status_code, 200)
        self.assertFalse(EducationLevel.objects.filter(id=self.level_2.id).exists())
