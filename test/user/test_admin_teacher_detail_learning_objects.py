"""Pruebas de universidad, sede y OA en el detalle administrativo del docente.

Cubre:
- `university` y `campus` con `{id, name}`, o `null` si no están asignados
- `learning_objects` con todos los OA del docente (públicos y no públicos),
  del más reciente al más antiguo, con los totales de vistas y descargas
- la URL absoluta del avatar
- el número de consultas no depende de cuántos OA tenga el docente
- el listado administrativo no cambia
"""

import io
import shutil
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from applications.address.models import Campus, University
from applications.education_level.models import EducationLevel
from applications.interaction.models import Interaction, ViewInteraction
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import Administrator, Student, Teacher
from roabackend.settings import DOMAIN
from test.helpers.temp_media_root import build_test_media_root


class AdminTeacherDetailLearningObjectsTests(TestCase):
    """Valida los campos nuevos de `teacher-to-approve/<id>` y `teacher-to-disapproved/<id>`."""

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-admin-teacher-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.admin_user = self.user_model.objects.create_admin_user(
            email="admin-teacher-detail@example.com",
            first_name="Admin",
            last_name="Detalle",
            password="StrongPass123",
        )
        self.admin_user.administrator = Administrator.objects.create(
            country="EC",
            city="Cuenca",
            phone=999999999,
            observation="Admin detalle docente",
            is_active=True,
        )
        self.admin_user.save()

        self.teacher_user = self.user_model.objects.create_general_user(
            email="teacher-admin-detail@example.com",
            first_name="Juan",
            last_name="Perez",
            password="StrongPass123",
        )
        self.teacher_user.teacher = Teacher.objects.create(is_active=False, is_account_active=True)
        self.teacher_user.save()

        self.education_level = EducationLevel.objects.create(name_es="Nivel Detalle", name_en="Detail Level")
        self.knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Detalle",
            description_es="Desc",
            name_en="Detail Area",
            description_en="Desc",
        )
        self.license = License.objects.create(
            name_es="Licencia Detalle",
            name_en="Detail License",
            value="DETAIL-LICENSE",
        )

        self.client.force_authenticate(self.admin_user)

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def detail_url(self, prefix="teacher-to-approve"):
        return f"/api/v1/{prefix}/{self.teacher_user.id}/"

    def assign_university_and_campus(self):
        university = University.objects.create(name="Universidad Politécnica Salesiana")
        campus = Campus.objects.create(name="El Vecino", address="Calle Vieja", university=university)
        self.teacher_user.university = university
        self.teacher_user.campus = campus
        self.teacher_user.save()
        return university, campus

    def _build_avatar_png(self):
        image_bytes = io.BytesIO()
        Image.new("RGB", (1, 1), color="white").save(image_bytes, format="PNG")
        return SimpleUploadedFile("avatar-admin-detail.png", image_bytes.getvalue(), content_type="image/png")

    def create_learning_object(self, title, public=True, user=None):
        learning_object_file = LearningObjectFile.objects.create(
            file=SimpleUploadedFile("admin-detail-oa.zip", b"zip-content", content_type="application/zip"),
            url="http://localhost/media/oazip/admin-detail-oa.zip",
            file_name="admin-detail-oa",
            file_size=11,
            path_origin="catalog/admin-detail-oa",
        )
        return LearningObjectMetadata.objects.create(
            learning_object_file=learning_object_file,
            adaptation="yes",
            avatar=self._build_avatar_png(),
            general_title=title,
            general_language="es",
            education_levels=self.education_level,
            knowledge_area=self.knowledge_area,
            license=self.license,
            user_created=user or self.teacher_user,
            public=public,
        )

    def create_student(self, email):
        user = self.user_model.objects.create_general_user(
            email=email,
            first_name="Estudiante",
            last_name="Detalle",
            password="StrongPass123",
        )
        user.student = Student.objects.create(has_disability=False, is_active=True, is_account_active=True)
        user.save()
        return user

    def test_university_and_campus_are_included(self):
        university, campus = self.assign_university_and_campus()

        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["university"], {"id": university.id, "name": university.name})
        self.assertEqual(response.data["campus"], {"id": campus.id, "name": campus.name})

    def test_university_and_campus_are_null_when_missing(self):
        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["university"])
        self.assertIsNone(response.data["campus"])

    def test_learning_objects_include_public_and_private_with_counters(self):
        older = self.create_learning_object("OA Público", public=True)
        newer = self.create_learning_object("OA En revisión", public=False)
        # Fechas fijas: dos OA creados seguidos pueden quedar con el mismo `created`.
        LearningObjectMetadata.objects.filter(pk=older.pk).update(created=timezone.now() - timedelta(days=1))
        # Dos filas de vistas para el mismo OA (flujo anterior) se suman.
        ViewInteraction.objects.create(learning_object=older, view=2)
        ViewInteraction.objects.create(learning_object=older, view=1)
        Interaction.objects.create(learning_object=older, user=self.create_student("a@example.com"), downloaded=1)
        Interaction.objects.create(learning_object=older, user=self.create_student("b@example.com"), downloaded=2)

        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        learning_objects = response.data["learning_objects"]
        self.assertEqual([item["id"] for item in learning_objects], [newer.id, older.id])
        self.assertFalse(learning_objects[0]["public"])
        self.assertEqual(learning_objects[0]["views"], 0)
        self.assertEqual(learning_objects[0]["downloads"], 0)
        self.assertTrue(learning_objects[1]["public"])
        self.assertEqual(learning_objects[1]["views"], 3)
        self.assertEqual(learning_objects[1]["downloads"], 3)
        self.assertEqual(learning_objects[1]["slug"], older.slug)
        self.assertEqual(learning_objects[1]["general_title"], "OA Público")
        self.assertTrue(learning_objects[1]["avatar"].startswith(DOMAIN))

    def test_learning_objects_exclude_other_users(self):
        other_teacher = self.user_model.objects.create_general_user(
            email="other-teacher-detail@example.com",
            first_name="Otro",
            last_name="Docente",
            password="StrongPass123",
        )
        self.create_learning_object("OA de otro docente", user=other_teacher)

        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["learning_objects"], [])

    def test_disapproved_route_also_includes_new_fields(self):
        self.assign_university_and_campus()
        self.create_learning_object("OA Ruta desaprobados")

        response = self.client.get(self.detail_url("teacher-to-disapproved"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["university"]["name"], "Universidad Politécnica Salesiana")
        self.assertEqual(len(response.data["learning_objects"]), 1)

    def test_query_count_does_not_grow_with_learning_objects(self):
        self.assign_university_and_campus()
        self.create_learning_object("OA Uno")
        with CaptureQueriesContext(connection) as one_learning_object:
            self.client.get(self.detail_url())

        for index in range(3):
            self.create_learning_object(f"OA Extra {index}")
        with CaptureQueriesContext(connection) as many_learning_objects:
            response = self.client.get(self.detail_url())

        self.assertEqual(len(response.data["learning_objects"]), 4)
        self.assertEqual(len(many_learning_objects), len(one_learning_object))

    def test_list_does_not_include_new_fields(self):
        self.assign_university_and_campus()
        self.create_learning_object("OA Listado")

        response = self.client.get("/api/v1/teacher-to-approve/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        for field in ("university", "campus", "learning_objects"):
            self.assertNotIn(field, response.data["results"][0])
