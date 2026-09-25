"""Pruebas de escenarios inválidos durante el upload de OAs comprimidos.

Esta suite comprueba que el endpoint rechaza paquetes que no cumplen con lo
mínimo esperado para un OA web:
- archivos que ni siquiera son ZIP validos
- paquetes sin metadata IMS/SCORM
- paquetes sin archivo de entrada web
- manifiestos XML corruptos

también protege la limpieza de archivos temporales cuando el upload falla.
"""

import io
import os
import shutil
import zipfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from applications.learning_object_file.models import LearningObjectFile
from applications.user.models import Teacher
from test.helpers.temp_media_root import build_test_media_root


class LearningObjectUploadErrorTests(TestCase):
    """Cubre rechazos controlados del endpoint de upload."""

    def setUp(self):
        """Prepara cliente docente autenticado y un MEDIA_ROOT temporal.

        Todas las pruebas de esta suite fuerzan errores, así que se aísla el
        directorio de media para comprobar también que no quede basura física
        después de un fallo.
        """
        # Aislamos media para que los fallos de upload no contaminen otros tests.
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-upload-errors-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()
        self._create_teacher_user()
        self._login_and_set_bearer("teacher-errors@example.com", "StrongPass123")

    def tearDown(self):
        """Limpia configuración temporal y archivos generados por la suite."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create_teacher_user(self):
        """Crea un usuario docente valido para consumir el endpoint protegido."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-errors@example.com",
            first_name="Teacher",
            last_name="Errors",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _login_and_set_bearer(self, email, password):
        """Realiza login y deja el token JWT en el cliente de pruebas."""
        login_response = self.client.post(
            "/api/v1/login/",
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

    def _build_zip_upload(self, filename, files):
        """Construye un ZIP en memoria con la estructura exacta del caso."""
        # Construimos ZIPs en memoria para simular escenarios malformados.
        zip_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_bytes, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for path, content in files.items():
                zip_file.writestr(path, content)
        zip_bytes.seek(0)
        return SimpleUploadedFile(
            filename,
            zip_bytes.read(),
            content_type="application/zip",
        )

    def _assert_scorm_error_response(self, response):
        """Valida la respuesta estándar cuando el OA no cumple IMS/SCORM.

        Todas las variantes invalidas de la suite convergen en este mismo
        formato de error, por eso se centraliza aquí la aserción.
        """
        # Todas las variantes invalidas deben responder con error SCORM/IMS.
        self.assertEqual(response.status_code, 404, response.data)
        self.assertIn("IMS y SCORM", response.data["message"])
        self.assertIn("data", response.data)
        self.assertTrue(response.data["data"]["scorm"])
        self.assertEqual(LearningObjectFile.objects.count(), 0)

    def _list_media_files(self):
        """Lista archivos físicos dentro de MEDIA_ROOT para validar limpieza."""
        files = []
        for root, _, filenames in os.walk(self.media_root):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, self.media_root).replace("\\", "/")
                files.append(relative_path)
        return sorted(files)

    def test_upload_rejects_invalid_zip_file(self):
        """Rechaza contenido que dice ser zip pero no tiene formato zip valido."""
        upload = SimpleUploadedFile(
            "invalid-oa.zip",
            b"not-a-zip",
            content_type="application/zip",
        )

        response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": upload},
            format="multipart",
        )

        self._assert_scorm_error_response(response)

    def test_upload_rejects_zip_without_imsmanifest_or_imslrm(self):
        """Rechaza zip que no incluye archivos de metadata imslrm/imsmanifest."""
        upload = self._build_zip_upload(
            "no-manifest.zip",
            {
                "index.html": "<html><body>content</body></html>",
                "assets/readme.txt": "no manifest metadata",
            },
        )

        response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": upload},
            format="multipart",
        )

        self._assert_scorm_error_response(response)

    def test_upload_rejects_zip_without_index_file(self):
        """Rechaza zip con metadata pero sin index o excursión para entrada web."""
        upload = self._build_zip_upload(
            "no-index.zip",
            {
                "imslrm.xml": "<lom></lom>",
                "assets/content.txt": "metadata exists but no index",
            },
        )

        response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": upload},
            format="multipart",
        )

        self._assert_scorm_error_response(response)

    def test_upload_rejects_zip_with_corrupted_manifest_structure(self):
        """Rechaza zip cuando el manifiesto XML existe pero esta corrupto."""
        upload = self._build_zip_upload(
            "corrupted-structure.zip",
            {
                "imsmanifest.xml": (
                    "<manifest><resources><resource>"
                    "<file href='index.html'></resource></resources>"
                ),
                "index.html": "<html><body>index</body></html>",
            },
        )

        response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": upload},
            format="multipart",
        )

        self._assert_scorm_error_response(response)

    def test_failed_upload_cleans_media_files_to_avoid_garbage(self):
        """Comprueba que un upload fallido no deje restos en `MEDIA_ROOT`."""
        upload = self._build_zip_upload(
            "cleanup-no-manifest.zip",
            {
                "index.html": "<html><body>sin manifest</body></html>",
                "assets/data.txt": "contenido de prueba",
            },
        )
        files_before = self._list_media_files()

        response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": upload},
            format="multipart",
        )

        self._assert_scorm_error_response(response)
        files_after = self._list_media_files()
        self.assertEqual(files_before, [])
        self.assertEqual(files_after, [])
