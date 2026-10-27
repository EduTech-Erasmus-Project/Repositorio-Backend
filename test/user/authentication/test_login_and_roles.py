"""Pruebas de creación por rol y login JWT del módulo `user`.

Este archivo mezcla dos comportamientos base del sistema:
- construcción de usuarios para cada rol soportado
- autenticación por login JWT para esas mismas cuentas

Sirve como documentación ejecutable del punto de entrada principal al módulo.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from applications.profession.models import Profession
from applications.user.models import Administrator, CollaboratingExpert, Student, Teacher


class UserRoleCreationTests(TestCase):
    """Verifica la creación de usuarios para cada rol soportado."""

    def setUp(self):
        """Carga el modelo de usuario para construir cuentas de prueba."""
        self.user_model = get_user_model()

    def test_create_student_user(self):
        """Crea un usuario estudiante y valida su relación y estado."""
        student = Student.objects.create(
            birthday=date(2000, 1, 1),
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-create@example.com",
            first_name="Student",
            last_name="Create",
            password="StrongPass123",
        )
        user.student = student
        user.save()

        self.assertIsNotNone(user.student)
        self.assertTrue(user.student.is_active)
        self.assertTrue(user.student.is_account_active)

    def test_create_teacher_user(self):
        """Crea usuario docente y confirma asignación de profesión."""
        profession = Profession.objects.create(description="QA Teacher")
        teacher = Teacher.objects.create(
            is_active=True,
            is_account_active=True,
        )
        teacher.professions.add(profession)

        user = self.user_model.objects.create_general_user(
            email="teacher-create@example.com",
            first_name="Teacher",
            last_name="Create",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()

        self.assertIsNotNone(user.teacher)
        self.assertTrue(user.teacher.is_active)
        self.assertTrue(user.teacher.is_account_active)
        self.assertEqual(user.teacher.professions.count(), 1)

    def test_create_expert_user(self):
        """Crea usuario experto colaborador y valida flags activos."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Alto",
            web="https://example.com",
            academic_profile="PhD",
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="expert-create@example.com",
            first_name="Expert",
            last_name="Create",
            password="StrongPass123",
        )
        user.collaboratingExpert = expert
        user.save()

        self.assertIsNotNone(user.collaboratingExpert)
        self.assertTrue(user.collaboratingExpert.is_active)
        self.assertTrue(user.collaboratingExpert.is_account_active)

    def test_create_administrator_user(self):
        """Crea usuario administrador y valida enlazado del perfil."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=123456789,
            observation="Admin test",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email="administrator-create@example.com",
            first_name="Administrator",
            last_name="Create",
            password="StrongPass123",
        )
        user.administrator = administrator
        user.save()

        self.assertIsNotNone(user.administrator)
        self.assertTrue(user.administrator.is_active)

    def test_create_superuser_user(self):
        """Crea superusuario y valida privilegio is_superuser."""
        user = self.user_model.objects.create_superuser(
            email="superuser-create@example.com",
            first_name="Super",
            last_name="User",
            password="StrongPass123",
        )

        self.assertTrue(user.is_superuser)


class UserRoleLoginTests(TestCase):
    """Prueba autenticación por login JWT para todos los roles."""

    def setUp(self):
        """Inicializa cliente API, modelo de usuario y endpoint de login."""
        self.client = APIClient()
        self.user_model = get_user_model()
        self.login_url = "/api/v1/login/"

    def assert_login_ok(self, email, password):
        """Ejecuta el login y comprueba que la respuesta incluya ambos JWT."""
        response = self.client.post(
            self.login_url,
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_student_user(self):
        """Confirma login correcto para una cuenta estudiante activa."""
        student = Student.objects.create(
            birthday=date(2000, 1, 1),
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-login@example.com",
            first_name="Student",
            last_name="Login",
            password="StrongPass123",
        )
        user.student = student
        user.save()

        self.assert_login_ok("student-login@example.com", "StrongPass123")

    def test_login_teacher_user(self):
        """Confirma login correcto para una cuenta docente activa."""
        profession = Profession.objects.create(description="Login Teacher")
        teacher = Teacher.objects.create(
            is_active=True,
            is_account_active=True,
        )
        teacher.professions.add(profession)
        user = self.user_model.objects.create_general_user(
            email="teacher-login@example.com",
            first_name="Teacher",
            last_name="Login",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()

        self.assert_login_ok("teacher-login@example.com", "StrongPass123")

    def test_login_expert_user(self):
        """Confirma login correcto para una cuenta experta activa."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Alto",
            web="https://example.com",
            academic_profile="Login profile",
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="expert-login@example.com",
            first_name="Expert",
            last_name="Login",
            password="StrongPass123",
        )
        user.collaboratingExpert = expert
        user.save()

        self.assert_login_ok("expert-login@example.com", "StrongPass123")

    def test_login_administrator_user(self):
        """Confirma login correcto para una cuenta administradora activa."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=987654321,
            observation="Admin login",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email="administrator-login@example.com",
            first_name="Administrator",
            last_name="Login",
            password="StrongPass123",
        )
        user.administrator = administrator
        user.save()

        self.assert_login_ok("administrator-login@example.com", "StrongPass123")

    def test_login_superuser_user(self):
        """Confirma login correcto para cuenta con privilegios de superusuario."""
        self.user_model.objects.create_superuser(
            email="superuser-login@example.com",
            first_name="Super",
            last_name="Login",
            password="StrongPass123",
        )

        self.assert_login_ok("superuser-login@example.com", "StrongPass123")


class InactiveAccountLoginTests(TestCase):
    """Valida que el login informe por qué una cuenta no puede ingresar."""

    def setUp(self):
        """Inicializa cliente API, modelo de usuario y endpoint de login."""
        self.client = APIClient()
        self.user_model = get_user_model()
        self.login_url = "/api/v1/login/"
        self.password = "StrongPass123"

    def create_teacher_user(self, email, is_active, is_account_active):
        """Crea un docente con los flags de activación indicados."""
        teacher = Teacher.objects.create(
            is_active=is_active,
            is_account_active=is_account_active,
        )
        user = self.user_model.objects.create_general_user(
            email=email,
            first_name="Teacher",
            last_name="Inactive",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def login(self, email, password):
        """Ejecuta el login y devuelve la response."""
        return self.client.post(
            self.login_url,
            {"email": email, "password": password},
            format="json",
        )

    def test_login_account_not_verified_returns_403(self):
        """Correo sin verificar: 403 con code `account_not_verified`."""
        user = self.create_teacher_user("teacher-unverified@example.com", is_active=False, is_account_active=False)

        response = self.login(user.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertEqual(response.data["code"], "account_not_verified")
        self.assertEqual(response.data["detail"], "Account inactive user")
        self.assertNotIn("access", response.data)

    def test_login_account_pending_approval_returns_403(self):
        """Correo verificado pero sin aprobación: 403 con code `account_pending_approval`."""
        user = self.create_teacher_user("teacher-pending@example.com", is_active=False, is_account_active=True)

        response = self.login(user.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertEqual(response.data["code"], "account_pending_approval")
        self.assertEqual(response.data["detail"], "Inactive user")
        self.assertNotIn("access", response.data)

    def test_login_inactive_account_with_wrong_password_returns_401(self):
        """Con contraseña incorrecta se mantiene el 401 y no se revela el estado de la cuenta."""
        user = self.create_teacher_user("teacher-wrong-pass@example.com", is_active=False, is_account_active=False)

        response = self.login(user.email, "WrongPass123")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
        self.assertEqual(response.data["code"], "no_active_account")
        self.assertEqual(response.data["detail"], "No active account found with the given credentials")

    def test_login_unknown_email_returns_401_with_code(self):
        """Un correo inexistente responde igual que una contraseña incorrecta."""
        response = self.login("missing-user@example.com", self.password)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
        self.assertEqual(response.data["code"], "no_active_account")
