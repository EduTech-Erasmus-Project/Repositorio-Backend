"""Contract and regression tests for public routes in `interaction`.

This module mixes manual compatibility routes and public endpoints used by
frontend for likes, downloads, rankings and `interaction-ref`. After the alias
cleanup, three behaviors must stay documented:

- removed trailing-slash aliases now return 404
- canonical routes still work normally
- `interaction-ref` without slash redirects through middleware
"""

import io
import shutil
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.interaction.models import Interaction
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import Student, Teacher
from test.helpers.temp_media_root import build_test_media_root


class InteractionURLCompatibilityTests(TestCase):
    """Covers active contract, functional regression and removed aliases."""

    def setUp(self):
        """Build an isolated setup with one public OA and two user roles.

        A temporary `MEDIA_ROOT` is used because several serializers expose
        file-related fields and the module works with models linked to the OA.
        """
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-interaction-urls-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.teacher_user = self._create_teacher_user()
        self.student_user = self._create_student_user()
        self.learning_object = self._create_learning_object()

    def tearDown(self):
        """Restore `MEDIA_ROOT` and delete physical leftovers from the suite."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _build_avatar_png(self):
        """Generate a minimal valid PNG without depending on binary fixtures."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-interaction-url.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _create_teacher_user(self):
        """Create the teacher who owns the OA used by the suite."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-interaction-url@example.com",
            first_name="Teacher",
            last_name="InteractionURL",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_student_user(self):
        """Create the student who generates interactions over the public OA."""
        student = Student.objects.create(
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-interaction-url@example.com",
            first_name="Student",
            last_name="InteractionURL",
            password="StrongPass123",
        )
        user.student = student
        user.save()
        return user

    def _create_learning_object(self):
        """Build a minimal public OA for likes and ranking scenarios.

        The full upload flow is not needed here. A persisted metadata record
        with an attached file is enough to exercise the interaction routes.
        """
        education_level = EducationLevel.objects.create(
            name_es="Nivel Interaction URL",
            name_en="Interaction URL Level",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Interaction URL",
            description_es="Desc",
            name_en="Interaction URL Area",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Interaction URL",
            name_en="Interaction URL License",
            value="INTERACTION-URL-LICENSE",
        )
        learning_object_file = LearningObjectFile.objects.create(
            file=SimpleUploadedFile(
                "interaction-url-oa.zip", b"zip-content", content_type="application/zip"
            ),
            url="http://localhost/media/oazip/interaction-url-oa.zip",
            file_name="interaction-url-oa",
            file_size=11,
            path_origin="catalog/interaction-url-oa",
        )
        return LearningObjectMetadata.objects.create(
            learning_object_file=learning_object_file,
            adaptation="yes",
            avatar=self._build_avatar_png(),
            general_title="OA Interaction URL",
            general_language="es",
            education_levels=education_level,
            knowledge_area=knowledge_area,
            license=license_obj,
            user_created=self.teacher_user,
            public=True,
        )

    def test_download_create_rejects_trailing_slash_alias(self):
        """Manual download creation no longer accepts the trailing-slash alias."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(
            "/api/v1/learning-objects/downloaded/",
            {"learning_object": self.learning_object.id, "downloaded": 0},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_download_update_rejects_trailing_slash_alias(self):
        """Manual download update also lost that alias.

        Besides the 404, the stored counter must remain unchanged.
        """
        interaction = Interaction.objects.create(
            liked=False,
            downloaded=2,
            learning_object=self.learning_object,
            user=self.student_user,
        )
        self.client.force_authenticate(user=self.student_user)
        response = self.client.put(
            f"/api/v1/learning-objects/downloaded/{self.learning_object.id}/",
            {"downloaded": interaction.downloaded},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        interaction.refresh_from_db()
        self.assertEqual(interaction.downloaded, 2)

    def test_liked_count_rejects_trailing_slash_alias(self):
        """Aggregated like count for an OA is exposed only without trailing slash."""
        Interaction.objects.create(
            liked=True,
            downloaded=0,
            learning_object=self.learning_object,
            user=self.student_user,
        )
        response = self.client.get(
            f"/api/v1/learning-objects/liked-count/{self.learning_object.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_most_liked_returns_results_on_canonical_route(self):
        """The canonical ranking route must keep returning valid results."""
        Interaction.objects.create(
            liked=True,
            downloaded=0,
            learning_object=self.learning_object,
            user=self.student_user,
        )
        response = self.client.get("/api/v1/learning-objects/most-liked/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.learning_object.id)

    def test_most_liked_returns_only_public_learning_objects(self):
        """The public ranking must never leak private OAs.

        A private OA with real likes is created to prove that the final public
        response still exposes only public objects.
        """
        private_learning_object = LearningObjectMetadata.objects.create(
            learning_object_file=LearningObjectFile.objects.create(
                file=SimpleUploadedFile(
                    "interaction-url-private-oa.zip",
                    b"zip-content",
                    content_type="application/zip",
                ),
                url="http://localhost/media/oazip/interaction-url-private-oa.zip",
                file_name="interaction-url-private-oa",
                file_size=11,
                path_origin="catalog/interaction-url-private-oa",
            ),
            adaptation="yes",
            avatar=self._build_avatar_png(),
            general_title="OA Interaction URL Privado",
            general_language="es",
            education_levels=self.learning_object.education_levels,
            knowledge_area=self.learning_object.knowledge_area,
            license=self.learning_object.license,
            user_created=self.teacher_user,
            public=False,
        )

        Interaction.objects.create(
            liked=True,
            downloaded=0,
            learning_object=self.learning_object,
            user=self.student_user,
        )
        Interaction.objects.create(
            liked=True,
            downloaded=0,
            learning_object=private_learning_object,
            user=self.teacher_user,
        )

        response = self.client.get("/api/v1/learning-objects/most-liked/")
        self.assertEqual(response.status_code, 200, response.data)
        ids = [item["id"] for item in response.data]
        self.assertIn(self.learning_object.id, ids)
        self.assertNotIn(private_learning_object.id, ids)

    @patch("applications.interaction.views.get_key_ref", return_value="secretref")
    def test_interaction_ref_redirects_request_without_trailing_slash(self, _mock_key_ref):
        """Without slash, Django redirects to the canonical route via middleware."""
        response = self.client.post(
            "/api/v1/interaction-ref",
            {"key_ref": "secretref"},
            format="json",
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/api/v1/interaction-ref/")

    @patch("applications.interaction.views.get_key_ref", return_value=None)
    def test_interaction_ref_without_config_returns_controlled_error(self, _mock_key_ref):
        """If `KEY_REF` is missing, the view returns a controlled legacy error.

        The goal is to guarantee the missing env var does not degrade into a
        500 response for existing consumers.
        """
        response = self.client.post(
            "/api/v1/interaction-ref/",
            {"key_ref": "secretref"},
            format="json",
        )
        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(response.data["message"], "Error")
