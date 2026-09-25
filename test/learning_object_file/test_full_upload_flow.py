"""Pruebas del flujo principal de `learning_object_file`.

Esta suite cubre el recorrido más representativo del módulo:
- login del docente
- upload de un OA desde un ZIP real de fixture
- creación de metadata asociada
- consulta posterior del OA por id y por slug

también valida dos reglas importantes:
- un usuario que no sea docente no puede subir OAs
- si falla la evaluación automática durante la creación de metadata, no debe
  quedar metadata parcial persistida
"""

import io
import shutil
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.evaluation_collaborating_expert.models import EvaluationConcept
from applications.knowledge_area.models import KnowledgeArea
from applications.license.models import License
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.user.models import Student, Teacher
from test.helpers.oa_real_zip_utils import (
    build_metadata_payload_from_upload,
    build_real_zip_upload_file,
)
from test.helpers.temp_media_root import build_test_media_root


class LearningObjectFullFlowTests(TestCase):
    """Cubre el flujo end-to-end mas importante del módulo de upload."""

    def setUp(self):
        """Inicializa cliente API y MEDIA_ROOT temporal aislado.

        La suite trabaja con archivos reales de prueba, por eso se aísla el
        directorio de media para que cada caso pueda crear y borrar contenido
        sin contaminar otras pruebas.
        """
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

    def tearDown(self):
        """Restaura settings y limpia archivos temporales creados por la suite."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _build_real_zip_from_fixture(self):
        """Carga el ZIP real de fixture o falla explícitamente si no existe."""
        try:
            return build_real_zip_upload_file()
        except FileNotFoundError as exc:
            self.fail(str(exc))

    def _build_avatar_png(self):
        """Genera un avatar PNG mínimo para el multipart de metadata."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _create_teacher_user(self):
        """Crea el docente autorizado para subir el OA base."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-flow@example.com",
            first_name="Teacher",
            last_name="Flow",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_student_user(self):
        """Crea un estudiante para comprobar permisos denegados en upload."""
        student = Student.objects.create(
            birthday=date(2000, 1, 1),
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-flow@example.com",
            first_name="Student",
            last_name="Flow",
            password="StrongPass123",
        )
        user.student = student
        user.save()
        return user

    def _login_and_set_bearer_token(self, email, password):
        """Autentica el cliente y fija el bearer token JWT correspondiente."""
        login_response = self.client.post(
            "/api/v1/login/",
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @patch(
        "applications.learning_object_metadata.views.mail_upload_OA_Satisfy_User.sendMail_Satisfay_User"
    )
    @patch(
        "applications.learning_object_metadata.views.mail_upload_OA_Not_Satisfy_User.sendMail_Not_Satisfay_User"
    )
    @patch(
        "applications.learning_object_metadata.views.mail_upload_OA_Not_Satisfy.sendMail_Not_Satisfay_Admin"
    )
    @patch(
        "applications.learning_object_metadata.views.mail_upload_OA_Satisfy.sendMailCreateOA"
    )
    def test_teacher_full_flow_login_upload_create_metadata_and_retrieve(
        self,
        _mock_mail_satisfy_admin,
        _mock_mail_not_satisfy_admin,
        _mock_mail_not_satisfy_user,
        _mock_mail_satisfy_user,
    ):
        """Verifica el flujo feliz completo desde upload hasta consulta final.

        La prueba asegura que:
        - el upload devuelve el `oa_file`
        - la metadata se crea correctamente sobre ese archivo
        - el OA puede consultarse por id y por slug
        - el registro final queda asociado al docente autenticado
        """
        teacher_user = self._create_teacher_user()
        self._login_and_set_bearer_token("teacher-flow@example.com", "StrongPass123")

        upload_response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": self._build_real_zip_from_fixture()},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.data)
        self.assertIn("oa_file", upload_response.data)
        uploaded_file_id = upload_response.data["oa_file"]["id"]

        education_level = EducationLevel.objects.create(
            name_es="Primaria Flujo",
            name_en="Primary Flow",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Matematica Flujo",
            description_es="Desc",
            name_en="Math Flow",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Flujo",
            name_en="Flow License",
            value="FLOW-LICENSE",
        )
        # automaticEvaluation divides by number of concepts; keep at least one.
        EvaluationConcept.objects.create(concept="Concepto QA")

        metadata_payload = build_metadata_payload_from_upload(
            upload_response.data,
            education_level_id=education_level.id,
            knowledge_area_id=knowledge_area.id,
            license_id=license_obj.id,
            avatar_file=self._build_avatar_png(),
        )

        metadata_create_response = self.client.post(
            "/api/v1/learning-object-metadata/",
            metadata_payload,
            format="multipart",
        )
        self.assertEqual(
            metadata_create_response.status_code, 201, metadata_create_response.data
        )
        self.assertIn("id", metadata_create_response.data)
        metadata_id = metadata_create_response.data["id"]
        metadata_slug = metadata_create_response.data["slug"]

        created_metadata = LearningObjectMetadata.objects.get(id=metadata_id)
        self.assertEqual(created_metadata.learning_object_file_id, uploaded_file_id)
        self.assertEqual(created_metadata.user_created_id, teacher_user.id)
        self.assertEqual(
            created_metadata.general_title,
            metadata_payload["general_title"],
        )

        metadata_retrieve_response = self.client.get(
            f"/api/v1/learning-object-metadata/{metadata_id}/"
        )
        self.assertEqual(metadata_retrieve_response.status_code, 200)
        self.assertEqual(metadata_retrieve_response.data["id"], metadata_id)

        slug_response = self.client.get(f"/api/v1/learning-object/{metadata_slug}/")
        self.assertEqual(slug_response.status_code, 200)
        self.assertEqual(slug_response.data["slug"], metadata_slug)

    def test_non_teacher_cannot_upload_learning_object_file(self):
        """Confirma que un estudiante no puede usar el endpoint de upload."""
        self._create_student_user()
        self._login_and_set_bearer_token("student-flow@example.com", "StrongPass123")

        response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": self._build_real_zip_from_fixture()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 403)

    @patch("applications.learning_object_metadata.views.automaticEvaluation", side_effect=RuntimeError("fallo forzado en evaluacion automatica"))
    def test_metadata_create_rolls_back_if_automatic_evaluation_fails(self, _mock_automatic_evaluation):
        """Protege el rollback si falla la evaluación automática.

        El upload del archivo ya existe, pero la metadata no debe persistirse si
        el paso de evaluación automática lanza una excepción en medio del flujo.
        """
        self._create_teacher_user()
        self._login_and_set_bearer_token("teacher-flow@example.com", "StrongPass123")

        upload_response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": self._build_real_zip_from_fixture()},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.data)

        education_level = EducationLevel.objects.create(
            name_es="Primaria Rollback",
            name_en="Primary Rollback",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Rollback",
            description_es="Desc",
            name_en="Rollback Area",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Rollback",
            name_en="Rollback License",
            value="ROLLBACK-LICENSE",
        )

        metadata_payload = build_metadata_payload_from_upload(
            upload_response.data,
            education_level_id=education_level.id,
            knowledge_area_id=knowledge_area.id,
            license_id=license_obj.id,
            avatar_file=self._build_avatar_png(),
        )

        with self.assertRaises(RuntimeError):
            self.client.post(
                "/api/v1/learning-object-metadata/",
                metadata_payload,
                format="multipart",
            )

        self.assertEqual(LearningObjectMetadata.objects.count(), 0)
