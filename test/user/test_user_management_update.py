"""Pruebas de regresión del endpoint `user-management`.

Este archivo cubre dos caminos sensibles del update de perfiles:
- actualización de estudiante con campos de ubicación nulos
- actualización de docente manteniendo IDs de ciudad, universidad y campus

La suite existe para proteger cambios recientes en serializers y validaciones
que ya rompieron estos payloads en el pasado.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.address.models import Campus, City, Country, Province, University
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
        country = Country.objects.create(name="Ecuador")
        province = Province.objects.create(name="Pichincha", country=country)
        city = City.objects.create(name="Quito", province=province)
        university = University.objects.create(name="UPS", country=country)
        campus = Campus.objects.create(
            name="Sur",
            address="Av. Moran",
            university=university,
            city=city,
        )
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
        user.country = country
        user.province = province
        user.city = city
        user.university = university
        user.campus = campus
        user.save()
        return user, profession, city, university, campus

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
            "city": None,
            "university": None,
            "campus": None,
        }

        response = self.client.put(self.student_url.format(pk=user.id), payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user.refresh_from_db()
        student = user.student
        student.refresh_from_db()

        self.assertEqual(user.last_name, "After")
        self.assertIsNone(user.city_id)
        self.assertIsNone(user.university_id)
        self.assertIsNone(user.campus_id)
        self.assertEqual(student.disability_description, "")
        self.assertCountEqual(
            list(student.knowledge_areas.values_list("id", flat=True)),
            [self.knowledge_area_1.id, self.knowledge_area_2.id],
        )
        self.assertCountEqual(
            list(student.preferences.values_list("id", flat=True)),
            [self.preference_1.id, self.preference_2.id],
        )

    def test_teacher_update_still_accepts_location_ids(self):
        """El update de docente debe seguir aceptando IDs validos de ubicación."""
        user, profession, city, university, campus = self._create_teacher_user()
        self.client.force_authenticate(user=user)

        payload = {
            "roles": ["teacher"],
            "first_name": "Teacher",
            "last_name": "After",
            "city": city.id,
            "university": university.id,
            "campus": campus.id,
            "professions": [profession.id],
        }

        response = self.client.put(self.student_url.format(pk=user.id), payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user.refresh_from_db()
        self.assertEqual(user.last_name, "After")
        self.assertEqual(user.city_id, city.id)
        self.assertEqual(user.university_id, university.id)
        self.assertEqual(user.campus_id, campus.id)
