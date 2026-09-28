"""Pruebas completas del catálogo `knowledge_area`.

Esta suite cubre tres frentes del módulo:
- localización del listado según `Accept-Language`
- permisos por rol para create, update, patch y delete
- validaciones básicas del CRUD, como requeridos y unicidad

La idea es que un cambio en vistas, serializers o permisos del catálogo rompa
una prueba si modifica el comportamiento esperado del API.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.knowledge_area.models import KnowledgeArea
from applications.user.models import Administrator, Teacher


class KnowledgeAreaFullFlowTests(TestCase):
    """Cubre localización, permisos y CRUD del catálogo de áreas."""

    def setUp(self):
        """Prepara áreas base y clientes autenticados por rol.

        La fixture crea dos knowledge áreas iniciales y cuatro clientes útiles
        para comparar comportamientos:
        - administrador
        - superusuario
        - docente sin permisos administrativos
        - anónimo para endpoints públicos
        """
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.area_1 = KnowledgeArea.objects.create(
            name_es="Matemáticas",
            description_es="Descripción matemáticas",
            name_en="Mathematics",
            description_en="Mathematics description",
        )
        self.area_2 = KnowledgeArea.objects.create(
            name_es="Física",
            description_es="Descripción física",
            name_en="Physics",
            description_en="Physics description",
        )

        self.admin_client = self._build_authenticated_client(self._create_admin_user())
        self.superuser_client = self._build_authenticated_client(self._create_superuser_user())
        self.teacher_client = self._build_authenticated_client(self._create_teacher_user())
        self.anonymous_client = APIClient()

    def _next_email(self, prefix):
        """Genera correos únicos para evitar conflictos entre pruebas."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _build_authenticated_client(self, user):
        """Autentica por JWT y retorna un cliente listo para consumir la API."""
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
        """Crea el administrador usado para operaciones permitidas."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin KnowledgeArea",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin"),
            first_name="Admin",
            last_name="KnowledgeArea",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_superuser_user(self):
        """Crea un superusuario para comparar permisos equivalentes."""
        return self.user_model.objects.create_superuser(
            email=self._next_email("superuser"),
            first_name="Super",
            last_name="KnowledgeArea",
            password=self.password,
        )

    def _create_teacher_user(self):
        """Crea docente para validar denegación en endpoints administrativos."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher"),
            first_name="Teacher",
            last_name="KnowledgeArea",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def test_list_without_accept_language_header_returns_message(self):
        """Verifica el mensaje explicito cuando falta `Accept-Language`."""
        response = self.anonymous_client.get("/api/v1/knowledge-area/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Accept Language in header is required")

    def test_list_in_spanish_returns_localized_values(self):
        """Comprueba la salida localizada en español del listado público.

        La prueba revisa el wrapper general del filtro y los nombres visibles
        por id dentro de `values`.
        """
        response = self.anonymous_client.get(
            "/api/v1/knowledge-area/",
            HTTP_ACCEPT_LANGUAGE="es",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["key"], "knowledge_area")
        self.assertEqual(response.data["filter_param_value"], "id")

        values_by_id = {value["id"]: value for value in response.data["values"]}
        self.assertEqual(values_by_id[self.area_1.id]["name"], "Matemáticas")
        self.assertEqual(values_by_id[self.area_2.id]["name"], "Física")

    def test_list_in_english_returns_localized_values(self):
        """Comprueba la salida localizada en ingles del listado público."""
        response = self.anonymous_client.get(
            "/api/v1/knowledge-area/",
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["key"], "knowledge_area")
        self.assertEqual(response.data["filter_param_value"], "id")

        values_by_id = {value["id"]: value for value in response.data["values"]}
        self.assertEqual(values_by_id[self.area_1.id]["name"], "Mathematics")
        self.assertEqual(values_by_id[self.area_2.id]["name"], "Physics")

    def test_list_with_unsupported_language_returns_406(self):
        """Valida el rechazo de idiomas no soportados por la vista."""
        response = self.anonymous_client.get(
            "/api/v1/knowledge-area/",
            HTTP_ACCEPT_LANGUAGE="fr",
        )
        self.assertEqual(response.status_code, 406, response.data)
        self.assertIn("message", response.data)

    def test_retrieve_is_public(self):
        """Asegura que el detalle por id siga siendo público."""
        response = self.anonymous_client.get(f"/api/v1/knowledge-area/{self.area_1.id}/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], self.area_1.id)
        self.assertEqual(response.data["name_es"], "Matemáticas")
        self.assertEqual(response.data["name_en"], "Mathematics")

    def test_create_requires_admin_permissions(self):        
        """Verifica que solo admin y superuser puedan crear nuevas áreas.

        El caso compara los tres escenarios importantes:
        - anónimo recibe 401
        - docente recibe 403
        - admin y superuser pueden crear correctamente
        """
        payload = {
            "name_es": "Química",
            "description_es": "Descripción química",
            "name_en": "Chemistry",
            "description_en": "Chemistry description",
        }

        anonymous_response = self.anonymous_client.post(
            "/api/v1/knowledge-area/",
            payload,
            format="json",
        )
        self.assertEqual(anonymous_response.status_code, 401)

        teacher_response = self.teacher_client.post(
            "/api/v1/knowledge-area/",
            payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/knowledge-area/",
            payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.data)

        super_response = self.superuser_client.post(
            "/api/v1/knowledge-area/",
            {
                "name_es": "Biología",
                "description_es": "Descripción biología",
                "name_en": "Biology",
                "description_en": "Biology description",
            },
            format="json",
        )
        self.assertEqual(super_response.status_code, 200, super_response.data)

    def test_create_validates_required_and_unique_fields(self):
        """Comprueba requeridos y unicidad al crear un área nueva."""
        missing_required = self.admin_client.post(
            "/api/v1/knowledge-area/",
            {"name_es": "Solo Español"},
            format="json",
        )
        self.assertEqual(missing_required.status_code, 400)
        self.assertIn("name_en", missing_required.data)

        duplicate = self.admin_client.post(
            "/api/v1/knowledge-area/",
            {
                "name_es": "Matemáticas",
                "description_es": "Desc",
                "name_en": "Mathematics",
                "description_en": "Desc",
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertTrue("name_es" in duplicate.data or "name_en" in duplicate.data)

    def test_update_requires_admin_and_persists_changes(self):
        """Comprueba que PUT requiere permisos altos y persiste cambios completos."""
        update_payload = {
            "name_es": "Matemáticas Avanzadas",
            "description_es": "Descripción actualizada",
            "name_en": "Advanced Mathematics",
            "description_en": "Updated description",
        }

        teacher_response = self.teacher_client.put(
            f"/api/v1/knowledge-area/{self.area_1.id}/",
            update_payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.put(
            f"/api/v1/knowledge-area/{self.area_1.id}/",
            update_payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.data)
        self.area_1.refresh_from_db()
        self.assertEqual(self.area_1.name_es, "Matemáticas Avanzadas")
        self.assertEqual(self.area_1.name_en, "Advanced Mathematics")

    def test_partial_update_requires_admin_and_persists_changes(self):
        """Comprueba que PATCH requiere permisos altos y persiste cambios parciales."""
        teacher_response = self.teacher_client.patch(
            f"/api/v1/knowledge-area/{self.area_1.id}/",
            {"description_es": "Docente no puede"},
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.patch(
            f"/api/v1/knowledge-area/{self.area_1.id}/",
            {"description_es": "Descripción parcial actualizada"},
            format="json",
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.data)
        self.area_1.refresh_from_db()
        self.assertEqual(self.area_1.description_es, "Descripción parcial actualizada")

    def test_delete_requires_admin_and_removes_record(self):
        """Comprueba que DELETE es administrativo y elimina el registro."""
        teacher_response = self.teacher_client.delete(f"/api/v1/knowledge-area/{self.area_2.id}/")
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.delete(f"/api/v1/knowledge-area/{self.area_2.id}/")
        self.assertEqual(admin_response.status_code, 200)
        self.assertFalse(KnowledgeArea.objects.filter(id=self.area_2.id).exists())
