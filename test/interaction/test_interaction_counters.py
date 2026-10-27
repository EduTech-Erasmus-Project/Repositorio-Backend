"""Pruebas de los contadores de vistas y descargas.

Cubre:
- `interaction-ref` emite referencias firmadas y limita la emisión por IP
- con referencia válida se suma una vez por referencia, por OA y por día
- referencias inventadas o alteradas no suman
- sin referencia se suma siempre 1 mientras esté permitido
- el número que envía el cliente se ignora
- las filas de vistas duplicadas se juntan en una
- descargas de un usuario sin fila previa sí se cuentan
- limpieza automática de los registros de días anteriores
"""

import io
import shutil
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.interaction.counters import issue_reference, read_reference
from applications.interaction.models import DownloadRecord, Interaction, ViewInteraction, ViewRecord
from applications.interaction.views import InteractionRefRateThrottle
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import Student, Teacher
from test.helpers.temp_media_root import build_test_media_root


class InteractionCountersTests(TestCase):
    """Valida las reglas para sumar vistas y descargas."""

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-counters-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.teacher_user = self._create_teacher_user()
        self.student_user = self._create_student_user()
        self.education_level = EducationLevel.objects.create(name_es="Nivel Contador", name_en="Counter Level")
        self.knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Contador",
            description_es="Desc",
            name_en="Counter Area",
            description_en="Desc",
        )
        self.license = License.objects.create(
            name_es="Licencia Contador",
            name_en="Counter License",
            value="COUNTER-LICENSE",
        )
        self.learning_object = self._create_learning_object("OA Contador Uno")
        self.other_learning_object = self._create_learning_object("OA Contador Dos")

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create_teacher_user(self):
        user = self.user_model.objects.create_general_user(
            email="teacher-counters@example.com",
            first_name="Teacher",
            last_name="Counters",
            password="StrongPass123",
        )
        user.teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user.save()
        return user

    def _create_student_user(self):
        user = self.user_model.objects.create_general_user(
            email="student-counters@example.com",
            first_name="Student",
            last_name="Counters",
            password="StrongPass123",
        )
        user.student = Student.objects.create(has_disability=False, is_active=True, is_account_active=True)
        user.save()
        return user

    def _build_avatar_png(self):
        image_bytes = io.BytesIO()
        Image.new("RGB", (1, 1), color="white").save(image_bytes, format="PNG")
        return SimpleUploadedFile("avatar-counters.png", image_bytes.getvalue(), content_type="image/png")

    def _create_learning_object(self, title):
        learning_object_file = LearningObjectFile.objects.create(
            file=SimpleUploadedFile("counters-oa.zip", b"zip-content", content_type="application/zip"),
            url="http://localhost/media/oazip/counters-oa.zip",
            file_name="counters-oa",
            file_size=11,
            path_origin="catalog/counters-oa",
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
            user_created=self.teacher_user,
            public=True,
        )

    def view(self, payload=None, learning_object=None):
        learning_object = learning_object or self.learning_object
        return self.client.put(
            f"/api/v1/learning-objects/viewed/{learning_object.id}",
            payload or {},
            format="json",
        )

    def download(self, payload=None, learning_object=None):
        learning_object = learning_object or self.learning_object
        self.client.force_authenticate(self.student_user)
        return self.client.put(
            f"/api/v1/learning-objects/downloaded/{learning_object.id}",
            payload or {},
            format="json",
        )

    def view_total(self, learning_object=None):
        learning_object = learning_object or self.learning_object
        return sum(ViewInteraction.objects.filter(learning_object=learning_object).values_list("view", flat=True))

    # Referencias

    @patch("applications.interaction.views.get_key_ref", return_value="secretref")
    def test_interaction_ref_returns_signed_reference(self, _mock_key_ref):
        response = self.client.post("/api/v1/interaction-ref/", {"key_ref": "secretref"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        self.assertIsNotNone(read_reference(response.data["reference"]))

    def test_tampered_or_invented_reference_is_rejected(self):
        reference = issue_reference()
        value, signature = reference.split(":")
        altered_char = "a" if value[-1] != "a" else "b"

        self.assertIsNone(read_reference(f"{value[:-1]}{altered_char}:{signature}"))
        self.assertIsNone(read_reference("a" * 64))
        self.assertIsNone(read_reference(""))

    @patch("applications.interaction.views.get_key_ref", return_value="secretref")
    def test_interaction_ref_is_throttled_by_ip(self, _mock_key_ref):
        with patch.object(InteractionRefRateThrottle, "THROTTLE_RATES", {"interaction_ref": "2/hour"}):
            statuses = [
                self.client.post("/api/v1/interaction-ref/", {"key_ref": "secretref"}, format="json").status_code
                for _ in range(3)
            ]

        self.assertEqual(statuses, [200, 200, 429])

    @patch("applications.interaction.views.get_key_ref", return_value="secretref")
    def test_interaction_ref_throttle_ignores_forged_forwarded_for(self, _mock_key_ref):
        # Como detrás de nginx (NUM_PROXIES=1): el cliente inventa una IP
        # distinta en cada petición y nginx agrega la real al final.
        with patch.object(InteractionRefRateThrottle, "THROTTLE_RATES", {"interaction_ref": "2/hour"}):
            statuses = [
                self.client.post(
                    "/api/v1/interaction-ref/",
                    {"key_ref": "secretref"},
                    format="json",
                    HTTP_X_FORWARDED_FOR=f"1.2.3.{forged}, 203.0.113.7",
                ).status_code
                for forged in range(3)
            ]

        self.assertEqual(statuses, [200, 200, 429])

    # Vistas

    def test_view_with_reference_counts_once_per_day(self):
        reference = issue_reference()

        first = self.view({"reference": reference})
        second = self.view({"reference": reference})

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data, [{"view": 1}])
        self.assertEqual(second.data, [{"view": 1}])
        self.assertEqual(ViewRecord.objects.count(), 1)

    def test_view_counts_for_other_reference_and_other_learning_object(self):
        reference = issue_reference()

        self.view({"reference": reference})
        self.view({"reference": issue_reference()})
        self.view({"reference": reference}, learning_object=self.other_learning_object)

        self.assertEqual(self.view_total(), 2)
        self.assertEqual(self.view_total(self.other_learning_object), 1)

    def test_view_with_invalid_reference_does_not_count(self):
        response = self.view({"reference": "a" * 64})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"view": 0}])
        self.assertFalse(ViewRecord.objects.exists())

    def test_view_without_reference_does_not_count(self):
        response = self.view()

        self.assertEqual(response.data, [{"view": 0}])

    def test_download_without_reference_does_not_count(self):
        response = self.download()

        self.assertEqual(response.data[0]["downloaded"], 0)

    @override_settings(INTERACTION_ALLOW_MISSING_REFERENCE=True)
    def test_view_without_reference_counts_when_allowed(self):
        self.view({"view": 5, "learning_object": self.learning_object.id})
        response = self.view({"view": 5, "learning_object": self.learning_object.id})

        self.assertEqual(response.data, [{"view": 2}])

    def test_view_ignores_number_sent_by_client(self):
        ViewInteraction.objects.create(learning_object=self.learning_object, view=10)

        response = self.view({"view": 99999, "reference": issue_reference()})

        self.assertEqual(response.data, [{"view": 11}])

    def test_view_uses_learning_object_from_url(self):
        self.view({"learning_object": self.other_learning_object.id, "reference": issue_reference()})

        self.assertEqual(self.view_total(), 1)
        self.assertEqual(self.view_total(self.other_learning_object), 0)

    def test_view_post_creates_single_counter(self):
        def payload():
            return {"learning_object": self.learning_object.id, "reference": issue_reference()}

        first = self.client.post("/api/v1/learning-objects/viewed", payload(), format="json")
        second = self.client.post("/api/v1/learning-objects/viewed", payload(), format="json")

        self.assertEqual(first.data, {"view": 1})
        self.assertEqual(second.data, {"view": 2})
        self.assertEqual(ViewInteraction.objects.filter(learning_object=self.learning_object).count(), 1)

    def test_view_merges_duplicated_counters(self):
        ViewInteraction.objects.create(learning_object=self.learning_object, view=3)
        ViewInteraction.objects.create(learning_object=self.learning_object, view=4)

        response = self.view({"reference": issue_reference()})

        self.assertEqual(response.data, [{"view": 8}])
        self.assertEqual(ViewInteraction.objects.filter(learning_object=self.learning_object).count(), 1)

    def test_view_get_returns_total_of_duplicated_counters(self):
        ViewInteraction.objects.create(learning_object=self.learning_object, view=3)
        ViewInteraction.objects.create(learning_object=self.learning_object, view=4)

        response = self.client.get(f"/api/v1/learning-objects/viewed/{self.learning_object.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"view": 7}])

    def test_view_get_without_counter_keeps_legacy_error(self):
        response = self.client.get(f"/api/v1/learning-objects/viewed/{self.learning_object.id}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": "error"})

    def test_view_unknown_learning_object_returns_404(self):
        response = self.client.put("/api/v1/learning-objects/viewed/999999", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Descargas

    def test_download_without_previous_interaction_is_counted(self):
        Interaction.objects.create(learning_object=self.learning_object, user=self.teacher_user, downloaded=4)

        response = self.download({"downloaded": 4, "reference": issue_reference()})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["downloaded"], 1)
        self.assertEqual(response.data[0]["user"], self.student_user.id)
        total = self.client.get(f"/api/v1/learning-objects/downloaded/{self.learning_object.id}")
        self.assertEqual(total.data, {"message": "success", "number": 5})

    def test_download_ignores_number_sent_by_client(self):
        Interaction.objects.create(learning_object=self.learning_object, user=self.student_user, downloaded=2)

        response = self.download({"downloaded": 99999, "reference": issue_reference()})

        self.assertEqual(response.data[0]["downloaded"], 3)

    def test_download_with_reference_counts_once_per_day(self):
        reference = issue_reference()

        self.download({"reference": reference})
        response = self.download({"reference": reference})

        self.assertEqual(response.data[0]["downloaded"], 1)
        self.assertEqual(DownloadRecord.objects.count(), 1)

    def test_download_with_invalid_reference_does_not_count(self):
        response = self.download({"reference": "inventada"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["downloaded"], 0)

    def test_download_post_keeps_count_and_returns_list(self):
        Interaction.objects.create(learning_object=self.learning_object, user=self.student_user, downloaded=2)
        self.client.force_authenticate(self.student_user)

        response = self.client.post(
            "/api/v1/learning-objects/downloaded",
            {"learning_object": self.learning_object.id, "reference": issue_reference()},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["downloaded"], 3)

    def test_download_requires_authentication(self):
        response = self.client.put(f"/api/v1/learning-objects/downloaded/{self.learning_object.id}", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Días y limpieza

    def test_same_reference_counts_again_next_day(self):
        reference = issue_reference()
        today = timezone.localdate()
        self.view({"reference": reference})

        with patch("applications.interaction.counters.timezone.localdate", return_value=today + timedelta(days=1)):
            response = self.view({"reference": reference})

        self.assertEqual(response.data, [{"view": 2}])

    def test_records_from_previous_days_are_cleaned_up(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        ViewRecord.objects.create(reference="v" * 64, learning_object=self.learning_object, date=yesterday)
        DownloadRecord.objects.create(reference="d" * 64, learning_object=self.learning_object, date=yesterday)

        self.view({"reference": issue_reference()})

        self.assertFalse(ViewRecord.objects.filter(date__lt=timezone.localdate()).exists())
        self.assertFalse(DownloadRecord.objects.exists())
        self.assertEqual(ViewRecord.objects.count(), 1)
