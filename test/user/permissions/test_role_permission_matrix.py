"""Pruebas de la matriz de permisos por rol del módulo `user`.

La suite recorre endpoints críticos del sistema y deja documentado que rol
puede intentarlos, incluso cuando el resultado esperado para el rol correcto es
un `400` por payload incompleto y no un `200`.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.user.models import Administrator, CollaboratingExpert, Student, Teacher


class RolePermissionMatrixTests(TestCase):
    """Matriz de permisos por rol para endpoints críticos de la API."""

    def setUp(self):
        """Crea usuarios por rol y un cliente por cada uno para validar permisos."""
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0
        self.clients = self._build_role_clients()

    def _build_role_clients(self):
        """Construye clientes autenticados para teacher, student, expert, admin y superuser."""
        users = {
            "teacher": self._create_teacher_user(),
            "student": self._create_student_user(),
            "expert": self._create_expert_user(),
            "admin": self._create_admin_user(),
            "superuser": self._create_superuser_user(),
        }
        clients = {}
        for role, user in users.items():
            clients[role] = self._create_authenticated_client(user.email)
        return clients

    def _next_email(self, prefix):
        """Genera correos únicos para evitar colisiones entre ejecuciones."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _create_teacher_user(self):
        """Crea un usuario con rol docente activo."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher"),
            first_name="Teacher",
            last_name="Matrix",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_student_user(self):
        """Crea un usuario con rol estudiante activo."""
        student = Student.objects.create(
            birthday=date(2000, 1, 1),
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email=self._next_email("student"),
            first_name="Student",
            last_name="Matrix",
            password=self.password,
        )
        user.student = student
        user.save()
        return user

    def _create_expert_user(self):
        """Crea un usuario con rol experto colaborador activo."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Alto",
            web="https://expert.local",
            academic_profile="QA profile",
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email=self._next_email("expert"),
            first_name="Expert",
            last_name="Matrix",
            password=self.password,
        )
        user.collaboratingExpert = expert
        user.save()
        return user

    def _create_admin_user(self):
        """Crea un usuario administrador activo."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin matrix",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin"),
            first_name="Admin",
            last_name="Matrix",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_superuser_user(self):
        """Crea un superusuario sin rol adicional."""
        return self.user_model.objects.create_superuser(
            email=self._next_email("superuser"),
            first_name="Super",
            last_name="Matrix",
            password=self.password,
        )

    def _create_authenticated_client(self, email):
        """Autentica cliente por JWT para ejecutar llamadas con un rol especifico."""
        client = APIClient()
        login_response = client.post(
            "/api/v1/login/",
            {"email": email, "password": self.password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        token = login_response.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    def _assert_matrix(self, method, url, data, expected_status_by_role, format_="json"):
        """Ejecuta una petición por rol y compara contra el estado esperado."""
        for role, expected_status in expected_status_by_role.items():
            client = self.clients[role]
            response = getattr(client, method)(url, data=data, format=format_)
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Rol '{role}' en {method.upper()} {url} respondio {response.status_code}, esperado {expected_status}.",
            )

    def test_learning_object_file_create_permissions(self):
        """Solo docente puede intentar la carga de archivo OA (otros 403)."""
        payload = {"file": "not-a-file"}
        expected = {
            "teacher": 400,
            "student": 403,
            "expert": 403,
            "admin": 403,
            "superuser": 403,
        }
        self._assert_matrix(
            method="post",
            url="/api/v1/learning-object-file/",
            data=payload,
            expected_status_by_role=expected,
            format_="multipart",
        )

    def test_learning_object_metadata_create_permissions(self):
        """Solo docente puede crear metadata (aunque falle validación de campos)."""
        expected = {
            "teacher": 400,
            "student": 403,
            "expert": 403,
            "admin": 403,
            "superuser": 403,
        }
        self._assert_matrix(
            method="post",
            url="/api/v1/learning-object-metadata/",
            data={},
            expected_status_by_role=expected,
            format_="multipart",
        )

    def test_student_evaluation_create_permissions(self):
        """Solo estudiante puede registrar evaluación de estudiante."""
        expected = {
            "teacher": 403,
            "student": 400,
            "expert": 403,
            "admin": 403,
            "superuser": 403,
        }
        self._assert_matrix(
            method="post",
            url="/api/v1/learning-objects/student-evaluation/",
            data={},
            expected_status_by_role=expected,
            format_="json",
        )

    def test_expert_evaluation_create_permissions(self):
        """Solo experto colaborador puede registrar evaluación de experto."""
        expected = {
            "teacher": 403,
            "student": 403,
            "expert": 400,
            "admin": 403,
            "superuser": 403,
        }
        self._assert_matrix(
            method="post",
            url="/api/v1/learning-objects/register-evaluation-expert/",
            data={},
            expected_status_by_role=expected,
            format_="json",
        )

    def test_evaluation_concept_create_permissions(self):
        """Solo admin/superuser pueden crear conceptos de evaluación."""
        expected = {
            "teacher": 403,
            "student": 403,
            "expert": 403,
            "admin": 201,
            "superuser": 201,
        }
        for role, expected_status in expected.items():
            concept_payload = {"concept": f"Concepto Permisos {role}"}
            client = self.clients[role]
            response = client.post(
                "/api/v1/object-learning-concept-evaluation/",
                concept_payload,
                format="json",
            )
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Rol '{role}' en creacion de concepto respondio {response.status_code}, esperado {expected_status}.",
            )

    def test_management_superuser_list_permissions(self):
        """Solo admin/superuser pueden listar administradores del sistema."""
        expected = {
            "teacher": 403,
            "student": 403,
            "expert": 403,
            "admin": 200,
            "superuser": 200,
        }
        self._assert_matrix(
            method="get",
            url="/api/v1/management-superuser/",
            data={},
            expected_status_by_role=expected,
            format_="json",
        )
