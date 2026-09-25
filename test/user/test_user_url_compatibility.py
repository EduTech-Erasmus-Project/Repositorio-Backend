"""Pruebas de contrato de rutas manuales del modulo `user`.

El módulo `user` tenía varios endpoints manuales de backoffice duplicados con y
sin slash final. Tras la limpieza del contrato se mantuvieron solo las formas
canónicas, por lo que estos tests dejan fijado que los aliases retirados:

- responden 404
- no ejecutan acciones destructivas
- no reabren la compatibilidad legacy sin decisión explícita
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.user.models import Administrator, CollaboratingExpert, Teacher, User


class UserURLCompatibilityTests(TestCase):
    """Caracteriza el rechazo actual de rutas legacy retiradas en `user`."""

    def setUp(self):
        """Prepara un admin autenticado y usuarios pendientes de aprobación.

        Las entidades desaprobadas se usan para validar que un alias de delete
        no borre datos si la ruta ya no forma parte del contrato activo.
        """
        self.client = APIClient()
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.admin_user = self._create_admin_user()
        self.client.force_authenticate(user=self.admin_user)
        self.teacher_user = self._create_disapproved_teacher_user()
        self.expert_user = self._create_disapproved_expert_user()

    def _next_email(self, prefix):
        """Genera correos únicos para evitar colisiones entre pruebas."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _create_admin_user(self):
        """Crea el administrador que consume los endpoints protegidos del módulo."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin user urls",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin-user-url"),
            first_name="Admin",
            last_name="UserURL",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_disapproved_teacher_user(self):
        """Crea un docente desaprobado para probar el alias legacy de delete."""
        teacher = Teacher.objects.create(is_active=False, is_account_active=False)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher-user-url"),
            first_name="Teacher",
            last_name="UserURL",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_disapproved_expert_user(self):
        """Crea un experto desaprobado para probar el alias legacy de delete."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Junior",
            web="https://example.com",
            academic_profile="Perfil",
            is_active=False,
            is_account_active=False,
        )
        user = self.user_model.objects.create_general_user(
            email=self._next_email("expert-user-url"),
            first_name="Expert",
            last_name="UserURL",
            password=self.password,
        )
        user.collaboratingExpert = expert
        user.save()
        return user

    def test_report_rejects_trailing_slash(self):
        """El endpoint manual de reportes ya no expone la variante con slash final."""
        response = self.client.get("/api/v1/report/")

        self.assertEqual(response.status_code, 404)

    def test_teacher_delete_rejects_trailing_slash(self):
        """El delete legacy de docente debe fallar sin tocar usuario ni perfil docente."""
        response = self.client.delete(
            f"/api/v1/teacher-to-approve-delete/{self.teacher_user.id}/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(User.objects.filter(pk=self.teacher_user.id).exists())
        self.assertTrue(Teacher.objects.filter(pk=self.teacher_user.teacher_id).exists())

    def test_expert_delete_rejects_trailing_slash(self):
        """El delete legacy de experto también debe fallar sin efectos secundarios."""
        response = self.client.delete(
            f"/api/v1/expert-to-approve-delete/{self.expert_user.id}/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(User.objects.filter(pk=self.expert_user.id).exists())
        self.assertTrue(
            CollaboratingExpert.objects.filter(
                pk=self.expert_user.collaboratingExpert_id
            ).exists()
        )
