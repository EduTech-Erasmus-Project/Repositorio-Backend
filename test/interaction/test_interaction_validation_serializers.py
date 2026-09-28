"""Pruebas de validación y rechazo de payloads en `interaction`.

Esta suite no se enfoca en compatibilidad de rutas, sino en algo más fino:
- que los serializers corten requests invalidos
- que un error de validación no deje cambios parciales en la base
- que contadores y registros existentes conserven su estado si el payload falla
"""

import io
import shutil

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.interaction.models import Interaction, ViewInteraction
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import Student, Teacher
from test.helpers.temp_media_root import build_test_media_root


class InteractionValidationSerializersTests(TestCase):
    """Cubre validaciones de entrada y protección contra mutaciones invalidas."""

    def setUp(self):
        """Prepara usuarios, OA base y media temporal para probar validaciones.

        La fixture monta un OA publico mínimo y usuarios suficientes para crear
        likes, descargas y vistas sin depender de otros módulos externos.
        """

        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-interaction-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.teacher_user = self._create_teacher_user()
        self.student_user = self._create_student_user()
        self.learning_object = self._create_learning_object()

    def tearDown(self):
        """Limpia el MEDIA_ROOT temporal creado por la suite."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _build_avatar_png(self):
        """Genera una imagen mínima para el avatar del OA base."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-interaction.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _create_teacher_user(self):
        """Crea el docente propietario del OA usado en validaciones."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-interaction@example.com",
            first_name="Teacher",
            last_name="Interaction",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_student_user(self):
        """Crea el estudiante que ejecuta interacciones autenticadas."""
        student = Student.objects.create(
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-interaction@example.com",
            first_name="Student",
            last_name="Interaction",
            password="StrongPass123",
        )
        user.student = student
        user.save()
        return user

    def _create_learning_object(self):
        """Crea un OA publico mínimo para likes, descargas y vistas."""
        education_level = EducationLevel.objects.create(
            name_es="Nivel Interaction",
            name_en="Interaction Level",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Interaction",
            description_es="Desc",
            name_en="Interaction Area",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Interaction",
            name_en="Interaction License",
            value="INTERACTION-LICENSE",
        )
        learning_object_file = LearningObjectFile.objects.create(
            file=SimpleUploadedFile("interaction-oa.zip", b"zip-content", content_type="application/zip"),
            url="http://localhost/media/oazip/interaction-oa.zip",
            file_name="interaction-oa",
            file_size=11,
            path_origin="catalog/interaction-oa",
        )
        return LearningObjectMetadata.objects.create(
            learning_object_file=learning_object_file,
            adaptation="yes",
            avatar=self._build_avatar_png(),
            general_title="OA Interaction",
            general_language="es",
            education_levels=education_level,
            knowledge_area=knowledge_area,
            license=license_obj,
            user_created=self.teacher_user,
            public=True,
        )

    def test_interaction_create_keeps_valid_flow(self):
        """Crear like con OA valido debe seguir funcionando igual."""
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            "/api/v1/object-learning/interaction/",
            {"learning_object": self.learning_object.id, "liked": True},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(
            Interaction.objects.filter(
                learning_object=self.learning_object,
                user=self.student_user,
                liked=True,
            ).exists()
        )

    def test_interaction_create_rejects_unknown_learning_object(self):
        """Si el OA no existe, el serializer corta el flujo antes de crear interacción."""
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            "/api/v1/object-learning/interaction/",
            {"learning_object": 999999, "liked": True},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Interaction.objects.count(), 0)

    def test_interaction_update_rejects_missing_liked_without_mutating_record(self):
        """Si falta liked, el update responde 400 y no altera el registro."""
        interaction = Interaction.objects.create(
            liked=False,
            downloaded=0,
            learning_object=self.learning_object,
            user=self.student_user,
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.put(
            f"/api/v1/object-learning/interaction/{interaction.id}/",
            {},
            format="json",
        )

        interaction.refresh_from_db()
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(interaction.liked)

    def test_download_counter_update_rejects_negative_values(self):
        """No permite payloads negativos al actualizar descargas."""
        interaction = Interaction.objects.create(
            liked=False,
            downloaded=3,
            learning_object=self.learning_object,
            user=self.student_user,
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.put(
            f"/api/v1/learning-objects/downloaded/{self.learning_object.id}",
            {"downloaded": -1},
            format="json",
        )

        interaction.refresh_from_db()
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(interaction.downloaded, 3)

    def test_view_interaction_update_rejects_negative_values(self):
        """No permite negativos en el contador de vistas del OA."""
        interaction_view = ViewInteraction.objects.create(
            view=5,
            learning_object=self.learning_object,
        )

        response = self.client.put(
            f"/api/v1/learning-objects/viewed/{self.learning_object.id}",
            {"view": -2, "learning_object": self.learning_object.id},
            format="json",
        )

        interaction_view.refresh_from_db()
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(interaction_view.view, 5)
