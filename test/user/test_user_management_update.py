"""Pruebas de regresión del endpoint `user-management`.

Este archivo cubre dos caminos sensibles del update de perfiles:
- actualización de estudiante con campos de ubicación nulos
- actualización de docente con la ubicación como texto (país, provincia,
  ciudad y universidad)

La suite existe para proteger cambios recientes en serializers y validaciones
que ya rompieron estos payloads en el pasado.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.preferences.models import Preferences, PreferencesArea
from applications.profession.models import Profession
from applications.user.models import Student, Teacher


class UserManagementUpdateTests(TestCase):
    """Cubre regressiones del update de perfiles en user-management."""

    def setUp(self):
        """Crea catálogos mínimos usados por updates de estudiante y docente."""
        self.client = APIClient()
        self.user_model = get_user_model()
        self.student_url = "/api/v1/user-management/{pk}/"

        self.education_level = EducationLevel.objects.create(
            name_es="Universitario",
            name_en="University",
        )
        self.knowledge_area_1 = KnowledgeArea.objects.create(
            name_es="Programacion",
            name_en="Programming",
        )
        self.knowledge_area_2 = KnowledgeArea.objects.create(
            name_es="Matematicas",
            name_en="Mathematics",
        )
        self.preference_area = PreferencesArea.objects.create(
            preferences_are="Accesibilidad",
        )
        self.preference_1 = Preferences.objects.create(
            description="Texto",
            priority=1,
            preferences_area=self.preference_area,
        )
        self.preference_2 = Preferences.objects.create(
            description="Visual",
            priority=2,
            preferences_area=self.preference_area,
        )

    def _create_student_user(self):
        """Crea un estudiante con relaciones iniciales para luego mutarlas vía PUT."""
        student = Student.objects.create(
            birthday=date(2000, 1, 2),
            has_disability=False,
            disability_description="",
            is_active=True,
            is_account_active=True,
        )
        student.education_levels.add(self.education_level)
        student.knowledge_areas.add(self.knowledge_area_1)
        student.preferences.add(self.preference_1)

        user = self.user_model.objects.create_general_user(
            email="student-update@example.com",
            first_name="Student",
            last_name="Before",
            password="StrongPass123",
        )
        user.student = student
        user.save()
        return user

    def _create_teacher_user(self):
        """Crea un docente con profesión y ubicación completas para el caso PUT."""
        profession = Profession.objects.create(description="Teacher Update")
        teacher = Teacher.objects.create(
            is_active=True,
            is_account_active=True,
        )
        teacher.professions.add(profession)

        user = self.user_model.objects.create_general_user(
            email="teacher-update@example.com",
            first_name="Teacher",
            last_name="Before",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.country_code = "EC"
        user.country_name = "Ecuador"
        user.province_code = "P"
        user.province_name = "Pichincha"
        user.city_name = "Quito"
        user.university_name = "UPS"
        user.save()
        return user, profession

    def test_student_update_accepts_null_location_fields_and_blank_disability_description(self):
        """El update de estudiante debe aceptar ubicación nula y descripción vacía."""
        user = self._create_student_user()
        self.client.force_authenticate(user=user)

        payload = {
            "roles": ["student"],
            "first_name": "Student",
            "last_name": "After",
            "birthday": "2000-01-02",
            "has_disability": "no",
            "disability_description": "",
            "education_levels": [self.education_level.id],
            "knowledge_areas": [self.knowledge_area_1.id, self.knowledge_area_2.id],
            "preferences": [self.preference_1.id, self.preference_2.id],
            "country_code": None,
            "country_name": None,
            "province_code": None,
            "province_name": None,
            "city_name": None,
            "university_name": None,
        }

        response = self.client.put(self.student_url.format(pk=user.id), payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user.refresh_from_db()
        student = user.student
        student.refresh_from_db()

        self.assertEqual(user.last_name, "After")
        self.assertEqual(user.country_code, "")
        self.assertEqual(user.city_name, "")
        self.assertEqual(user.university_name, "")
        self.assertEqual(student.disability_description, "")
        self.assertCountEqual(
            list(student.knowledge_areas.values_list("id", flat=True)),
            [self.knowledge_area_1.id, self.knowledge_area_2.id],
        )
        self.assertCountEqual(
            list(student.preferences.values_list("id", flat=True)),
            [self.preference_1.id, self.preference_2.id],
        )

    def test_teacher_update_saves_location_as_text(self):
        """El update de docente guarda la ubicación como texto y normaliza el país."""
        user, profession = self._create_teacher_user()
        self.client.force_authenticate(user=user)

        payload = {
            "roles": ["teacher"],
            "first_name": "Teacher",
            "last_name": "After",
            "country_code": "co",
            "country_name": "Colombia",
            "province_code": "ANT",
            "province_name": "Antioquia",
            "city_name": "Medellín",
            "university_name": "Universidad de Antioquia",
            "professions": [profession.id],
        }

        response = self.client.put(self.student_url.format(pk=user.id), payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user.refresh_from_db()
        self.assertEqual(user.last_name, "After")
        self.assertEqual(user.country_code, "CO")
        self.assertEqual(user.country_name, "Colombia")
        self.assertEqual(user.province_code, "ANT")
        self.assertEqual(user.province_name, "Antioquia")
        self.assertEqual(user.city_name, "Medellín")
        self.assertEqual(user.university_name, "Universidad de Antioquia")

    def test_teacher_update_without_location_keeps_saved_location(self):
        """Si el payload no trae ubicación, se conserva la guardada."""
        user, profession = self._create_teacher_user()
        self.client.force_authenticate(user=user)

        payload = {
            "roles": ["teacher"],
            "first_name": "Teacher",
            "last_name": "After",
            "professions": [profession.id],
        }

        response = self.client.put(self.student_url.format(pk=user.id), payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user.refresh_from_db()
        self.assertEqual(user.country_code, "EC")
        self.assertEqual(user.city_name, "Quito")
        self.assertEqual(user.university_name, "UPS")

    def test_teacher_update_rejects_invalid_country_code(self):
        """El código de país debe ser ISO de 2 letras."""
        user, profession = self._create_teacher_user()
        self.client.force_authenticate(user=user)

        payload = {
            "roles": ["teacher"],
            "first_name": "Teacher",
            "last_name": "After",
            "country_code": "ECU",
            "professions": [profession.id],
        }

        response = self.client.put(self.student_url.format(pk=user.id), payload, format="json")

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("country_code", response.data)
        user.refresh_from_db()
        self.assertEqual(user.country_code, "EC")
        self.assertEqual(user.last_name, "Before")
