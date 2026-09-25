"""Pruebas del filtro administrativo por rango de fechas en metadata OA.

Esta suite cubre el listado administrativo que mezcla OAs públicos y privados
y verifica un caso fino del filtro por `created`:
- el día final debe incluir cualquier hora de esa misma fecha
- el endpoint no debe emitir warnings por comparar datetimes naive contra
  valores aware

La prueba existe porque ese tipo de regresión suele aparecer al normalizar
fechas de entrada en filtros de administración.
"""

import io
import shutil
import warnings
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.learning_object_metadata.views import ListLearningObjectPublicAndPrivate
from applications.license.models import License
from applications.user.models import Administrator, Teacher
from test.helpers.temp_media_root import build_test_media_root


class AdminLearningObjectDateFilterTests(TestCase):
    """Verifica el filtro admin por fecha de creación de objetos de aprendizaje."""

    def setUp(self):
        """Crea usuarios y catálogos mínimos para probar el listado admin.

        La suite no necesita un flujo completo de upload. Solo prepara la
        metadata mínima necesaria para consultar el endpoint protegido y
        controlar de forma exacta las fechas de creación.
        """
        self.factory = APIRequestFactory()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-oa-admin-date-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()
        self._sequence = 0

        self.teacher_user = self._create_teacher_user()
        self.admin_user = self._create_admin_user()
        self.education_level = EducationLevel.objects.create(
            name_es="Primaria Fecha Admin",
            name_en="Primary Date Admin",
        )
        self.knowledge_area = KnowledgeArea.objects.create(
            name_es="Matematica Fecha Admin",
            description_es="Desc",
            name_en="Math Date Admin",
            description_en="Desc",
        )
        self.license = License.objects.create(
            name_es="Licencia Fecha Admin",
            name_en="Date Admin License",
            value="DATE-ADMIN-LICENSE",
        )

    def tearDown(self):
        """Limpia archivos temporales del MEDIA_ROOT de pruebas."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _next_email(self, prefix):
        """Genera correos únicos para evitar colisiones."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _create_teacher_user(self):
        """Crea un docente activo propietario de los OAs de prueba."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher-admin-date"),
            first_name="Teacher",
            last_name="AdminDate",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_admin_user(self):
        """Crea un administrador autenticable para el endpoint protegido."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin date filter",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin-date"),
            first_name="Admin",
            last_name="Date",
            password="StrongPass123",
        )
        user.administrator = administrator
        user.save()
        return user

    def _build_avatar_png(self):
        """Genera un avatar mínimo valido para metadata."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-admin-date.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _create_learning_object_file(self, seq):
        """Crea un archivo OA mínimo para asociar metadata."""
        return LearningObjectFile.objects.create(
            file=SimpleUploadedFile(f"oa-admin-date-{seq}.zip", b"PK\x03\x04"),
            url=f"http://testserver/media/catalog/oa-admin-date-{seq}/index.html",
            file_name=f"oa-admin-date-{seq}",
            file_size=1,
            path_origin=self.media_root,
        )

    def _create_metadata(self, title, public, created_at):
        """Crea metadata mínima y fija manualmente la fecha de creación.

        El endpoint filtra por `created`, asi que esta ayuda permite construir
        escenarios dentro y fuera del rango sin depender del reloj real.
        """
        self._sequence += 1
        metadata = LearningObjectMetadata.objects.create(
            learning_object_file=self._create_learning_object_file(self._sequence),
            adaptation="none",
            avatar=self._build_avatar_png(),
            general_title=title,
            general_description="Descripcion",
            general_language="es",
            education_levels=self.education_level,
            knowledge_area=self.knowledge_area,
            license=self.license,
            user_created=self.teacher_user,
            public=public,
            accesibility_features="captions",
            accesibility_hazard="noFlashingHazard",
            accesibility_control="fullkeyboardcontrol",
            annotation_modeaccess="Visual",
            annotation_modeaccesssufficient="",
            classification_purpose="",
        )
        LearningObjectMetadata.objects.filter(pk=metadata.pk).update(created=created_at)
        metadata.refresh_from_db()
        return metadata

    def test_admin_filter_by_created_date_includes_full_end_day_without_warning(self):
        """Incluye todo el día final del rango y evita warnings por naive datetime.

        El caso protege dos cosas a la vez:
        - que `created_end=2026-03-18` incluya un OA creado ese dia a las 15:30
        - que el filtro no vuelva a emitir el warning de Django sobre
          comparaciones entre datetimes naive y aware
        """
        in_range = self._create_metadata(
            title="OA dentro del rango",
            public=True,
            created_at=timezone.make_aware(datetime(2026, 3, 18, 15, 30, 0)),
        )
        self._create_metadata(
            title="OA fuera del rango",
            public=True,
            created_at=timezone.make_aware(datetime(2026, 3, 19, 9, 0, 0)),
        )
        self._create_metadata(
            title="OA privado del rango",
            public=False,
            created_at=timezone.make_aware(datetime(2026, 3, 18, 10, 0, 0)),
        )

        request = self.factory.get(
            "/api/v1/learning-objects-approved-and-disapproved/1/",
            {"created_init": "2026-03-18", "created_end": "2026-03-18"},
        )
        force_authenticate(request, user=self.admin_user)

        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            response = ListLearningObjectPublicAndPrivate.as_view()(request, public=1)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], in_range.id)
        naive_warnings = [
            warning for warning in captured_warnings
            if "naive datetime" in str(warning.message).lower()
        ]
        self.assertEqual(naive_warnings, [])
