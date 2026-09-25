"""Pruebas del borrado de OAs en `learning_object_file`.

El contrato actual mantiene solo las rutas canonicas sin slash final para los
delete manuales. Las variantes retiradas deben responder 404.
"""

import io
import os
import shutil
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.evaluation_collaborating_expert.models import EvaluationConcept
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import Administrator, Teacher
from test.helpers.oa_real_zip_utils import (
    build_metadata_payload_from_upload,
    build_real_zip_upload_file,
)
from test.helpers.temp_media_root import build_test_media_root


class AdminDeleteLearningObjectTests(TestCase):
    """Cubre borrado admin y borrado docente de objetos de aprendizaje."""

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.media_root = build_test_media_root("test-media-admin-delete-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.teacher_user = self._create_teacher_user()
        self.admin_user = self._create_admin_user()
        self.teacher_client = self._build_authenticated_client(self.teacher_user)
        self.admin_client = self._build_authenticated_client(self.admin_user)

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _next_email(self, prefix):
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _build_authenticated_client(self, user):
        client = APIClient()
        login_response = client.post(
            "/api/v1/login/",
            {"email": user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        return client

    def _create_teacher_user(self):
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher-delete"),
            first_name="Teacher",
            last_name="Delete",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_admin_user(self):
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin delete OA",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin-delete"),
            first_name="Admin",
            last_name="Delete",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _build_avatar_png(self):
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _build_real_zip_from_fixture(self):
        try:
            return build_real_zip_upload_file()
        except FileNotFoundError as exc:
            self.fail(str(exc))

    def _create_uploaded_learning_object(self):
        upload_response = self.teacher_client.post(
            "/api/v1/learning-object-file/",
            {"file": self._build_real_zip_from_fixture()},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.data)

        education_level = EducationLevel.objects.create(
            name_es="Primaria Delete",
            name_en="Primary Delete",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Matematica Delete",
            description_es="Desc",
            name_en="Math Delete",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Delete",
            name_en="Delete License",
            value="DELETE-LICENSE",
        )
        EvaluationConcept.objects.create(concept="Concepto Delete QA")

        metadata_payload = build_metadata_payload_from_upload(
            upload_response.data,
            education_level_id=education_level.id,
            knowledge_area_id=knowledge_area.id,
            license_id=license_obj.id,
            avatar_file=self._build_avatar_png(),
        )

        with patch(
            "applications.learning_object_metadata.views.mail_upload_OA_Satisfy_User.sendMail_Satisfay_User"
        ), patch(
            "applications.learning_object_metadata.views.mail_upload_OA_Not_Satisfy_User.sendMail_Not_Satisfay_User"
        ), patch(
            "applications.learning_object_metadata.views.mail_upload_OA_Not_Satisfy.sendMail_Not_Satisfay_Admin"
        ), patch(
            "applications.learning_object_metadata.views.mail_upload_OA_Satisfy.sendMailCreateOA"
        ):
            metadata_response = self.teacher_client.post(
                "/api/v1/learning-object-metadata/",
                metadata_payload,
                format="multipart",
            )

        self.assertEqual(metadata_response.status_code, 201, metadata_response.data)
        return LearningObjectMetadata.objects.get(pk=metadata_response.data["id"])

    @patch("applications.learning_object_file.views.mail_delete_oa.sendMailDeleteOA")
    def test_admin_delete_with_trailing_slash_returns_404(
        self,
        mock_send_mail_delete,
    ):
        metadata = self._create_uploaded_learning_object()
        learning_object = metadata.learning_object_file
        path_origin = learning_object.path_origin

        response = self.admin_client.delete(
            f"/api/v1/learning-object-file-delete-admin/{metadata.id}/?message=Motivo",
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(LearningObjectMetadata.objects.filter(pk=metadata.id).exists())
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object.id).exists())
        self.assertTrue(os.path.exists(path_origin))
        mock_send_mail_delete.assert_not_called()

    @patch("applications.learning_object_file.views.mail_delete_oa.sendMailDeleteOA")
    def test_admin_delete_without_trailing_slash_keeps_canonical_contract(
        self,
        mock_send_mail_delete,
    ):
        metadata = self._create_uploaded_learning_object()
        learning_object = metadata.learning_object_file
        path_origin = learning_object.path_origin

        response = self.admin_client.delete(
            f"/api/v1/learning-object-file-delete-admin/{metadata.id}?message=Motivo",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Record deleted successfully")
        self.assertFalse(LearningObjectMetadata.objects.filter(pk=metadata.id).exists())
        self.assertFalse(LearningObjectFile.objects.filter(pk=learning_object.id).exists())
        self.assertFalse(os.path.exists(path_origin))
        mock_send_mail_delete.assert_called_once()

    def test_teacher_delete_with_trailing_slash_returns_404(self):
        metadata = self._create_uploaded_learning_object()
        learning_object = metadata.learning_object_file
        path_origin = learning_object.path_origin

        response = self.teacher_client.delete(
            f"/api/v1/learning-object-file-delete/{learning_object.id}/",
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(LearningObjectMetadata.objects.filter(pk=metadata.id).exists())
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object.id).exists())
        self.assertTrue(os.path.exists(path_origin))

    def test_teacher_delete_without_trailing_slash_keeps_canonical_contract(self):
        metadata = self._create_uploaded_learning_object()
        learning_object = metadata.learning_object_file
        path_origin = learning_object.path_origin

        response = self.teacher_client.delete(
            f"/api/v1/learning-object-file-delete/{learning_object.id}",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["message"], "Record deleted successfully")
        self.assertFalse(LearningObjectMetadata.objects.filter(pk=metadata.id).exists())
        self.assertFalse(LearningObjectFile.objects.filter(pk=learning_object.id).exists())
        self.assertFalse(os.path.exists(path_origin))
