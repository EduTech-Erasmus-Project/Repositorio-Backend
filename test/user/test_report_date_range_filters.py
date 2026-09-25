"""Pruebas del filtro por rango de fechas en reportes del módulo `user`.

La suite se concentra en un caso fino del reporte administrativo de docentes:
el día final del rango debe incluir cualquier hora de esa fecha y no debe
reaparecer el warning por comparar datetimes naive y aware.
"""

import warnings
from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.user.models import Administrator, Teacher, User
from applications.user.views import ReportListAPIView


class UserReportDateFilterTests(TestCase):
    """Valida los filtros por fecha del reporte de usuarios docentes."""

    def setUp(self):
        """Crea usuarios admin y docentes para probar el rango por fecha."""
        self.factory = APIRequestFactory()
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0
        self.admin_user = self._create_admin_user()

    def _next_email(self, prefix):
        """Genera correos únicos por prueba."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _create_admin_user(self):
        """Crea administrador activo para consultar el reporte."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin report date",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin-report"),
            first_name="Admin",
            last_name="Report",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_teacher_user(self, email_prefix, created_at):
        """Crea un docente y fija manualmente su fecha de creación."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email(email_prefix),
            first_name="Teacher",
            last_name=email_prefix.title(),
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        User.objects.filter(pk=user.pk).update(created=created_at)
        user.refresh_from_db()
        return user

    def test_report_filter_by_created_date_includes_full_end_day_without_warning(self):
        """Incluye docentes creados en cualquier hora del día final y evita warnings naive."""
        in_range = self._create_teacher_user(
            "teacher-in-range",
            timezone.make_aware(datetime(2026, 3, 18, 18, 45, 0)),
        )
        self._create_teacher_user(
            "teacher-out-range",
            timezone.make_aware(datetime(2026, 3, 19, 8, 0, 0)),
        )

        request = self.factory.get(
            "/api/v1/report",
            {"created_init": "2026-03-18", "created_end": "2026-03-18"},
        )
        force_authenticate(request, user=self.admin_user)

        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            response = ReportListAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], in_range.email)
        naive_warnings = [
            warning for warning in captured_warnings
            if "naive datetime" in str(warning.message).lower()
        ]
        self.assertEqual(naive_warnings, [])
