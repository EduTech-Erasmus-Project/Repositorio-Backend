"""Pruebas del endpoint de notificacion administrativa de hallazgos del OA."""

import io
import shutil
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import Administrator, Teacher
from test.helpers.temp_media_root import build_test_media_root


class LearningObjectReviewNotificationEndpointTests(TestCase):
    """Verifica envio de hallazgos administrativos al docente creador del OA."""

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.media_root = build_test_media_root("test-media-oa-review-notification-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.teacher_user = self._create_teacher_user()
        self.admin_user = self._create_admin_user()
        self.teacher_client = self._build_authenticated_client(self.teacher_user)
        self.admin_client = self._build_authenticated_client(self.admin_user)
        self.learning_object = self._create_learning_object()

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _next_email(self, prefix):
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _build_authenticated_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def _build_avatar_png(self):
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-review-notification.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _build_zip_file(self):
        return SimpleUploadedFile(
            "oa-review-notification.zip",
            b"PK\x03\x04",
            content_type="application/zip",
        )

    def _create_teacher_user(self):
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher-review"),
            first_name="Teacher",
            last_name="Review",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_admin_user(self):
        administrator = Administrator.objects.create(
            country="EC",
            city="Cuenca",
            phone=999999999,
            observation="Admin review notification",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin-review"),
            first_name="Admin",
            last_name="Review",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_learning_object(self):
        education_level = EducationLevel.objects.create(
            name_es="Primaria Revision",
            name_en="Primary Review",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Matematica Revision",
            description_es="Desc",
            name_en="Math Review",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Revision",
            name_en="Review License",
            value="REVIEW-LICENSE",
        )
        learning_object_file = LearningObjectFile.objects.create(
            file=self._build_zip_file(),
            url="http://testserver/media/catalog/oa-review/index.html",
            file_name="oa-review",
            file_size=4,
            path_origin="media/catalog/oa-review",
        )
        return LearningObjectMetadata.objects.create(
            learning_object_file=learning_object_file,
            adaptation="No",
            avatar=self._build_avatar_png(),
            is_adapted_oer=False,
            general_title="OA con observaciones",
            general_language="es",
            general_description="Descripcion de prueba",
            education_levels=education_level,
            knowledge_area=knowledge_area,
            license=license_obj,
            user_created=self.teacher_user,
        )

    @patch("applications.learning_object_metadata.views.mail_learning_object_findings.sendMailFindings")
    def test_admin_can_notify_findings_to_teacher(self, send_mail_mock):
        response = self.admin_client.post(
            f"/api/v1/learning-objects-review-notification/{self.learning_object.id}/",
            {"message": "Debe corregir metadata y mejorar accesibilidad."},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Notification sent successfully")
        send_mail_mock.assert_called_once_with(
            self.teacher_user.email,
            "Teacher Review",
            self.learning_object.general_title,
            "Debe corregir metadata y mejorar accesibilidad.",
        )

    @patch("applications.learning_object_metadata.views.mail_learning_object_findings.sendMailFindings")
    def test_teacher_cannot_use_review_notification_endpoint(self, send_mail_mock):
        response = self.teacher_client.post(
            f"/api/v1/learning-objects-review-notification/{self.learning_object.id}/",
            {"message": "Intento no permitido."},
            format="json",
        )

        self.assertEqual(response.status_code, 403, response.data)
        send_mail_mock.assert_not_called()
