"""Pruebas de los endpoints públicos del perfil del docente.

- `GET /api/v1/authors/<user_key>/`
- `GET /api/v1/authors/<user_key>/learning-objects/`

Cubre los casos de 404 (iguales en ambos endpoints), el filtrado de campos
según su visibilidad y los totales de vistas y descargas por OA.
"""

import io
import shutil
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.interaction.models import Interaction, ViewInteraction
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.profession.models import Profession
from applications.user.models import AcademicDegree, PublicProfile, Student, Teacher, UserLink
from test.helpers.temp_media_root import build_test_media_root


class PublicAuthorAPITestBase(TestCase):
    """Crea un docente con un OA público y catálogos mínimos para los OA."""

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-public-author-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.education_level = EducationLevel.objects.create(name_es="Nivel Autor", name_en="Author Level")
        self.knowledge_area = KnowledgeArea.objects.create(
            name_es="Ingeniería", description_es="Desc", name_en="Engineering", description_en="Desc"
        )
        self.license = License.objects.create(
            name_es="Licencia Autor", name_en="Author License", value="AUTHOR-LICENSE"
        )
        self.oa_counter = 0

        self.author = self.create_teacher("author@example.com")
        self.public_oa = self.create_learning_object(self.author, public=True)

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def create_teacher(self, email, is_active=True):
        user = self.user_model.objects.create_general_user(
            email=email, first_name="Juan", last_name="Perez", password="StrongPass123"
        )
        user.teacher = Teacher.objects.create(is_active=is_active, is_account_active=True)
        user.save()
        return user

    def create_learning_object(self, user, public, knowledge_area=None):
        # Títulos distintos: el slug se genera con el título y la hora.
        self.oa_counter += 1
        image_bytes = io.BytesIO()
        Image.new("RGB", (1, 1), color="white").save(image_bytes, format="PNG")
        return LearningObjectMetadata.objects.create(
            learning_object_file=LearningObjectFile.objects.create(
                file=SimpleUploadedFile(f"author-oa-{self.oa_counter}.zip", b"zip", content_type="application/zip"),
                url=f"http://localhost/media/oazip/author-oa-{self.oa_counter}.zip",
                file_name=f"author-oa-{self.oa_counter}",
                file_size=3,
                path_origin=f"catalog/author-oa-{self.oa_counter}",
            ),
            adaptation="yes",
            avatar=SimpleUploadedFile("avatar.png", image_bytes.getvalue(), content_type="image/png"),
            general_title=f"OA del autor {self.oa_counter}",
            general_language="es",
            education_levels=self.education_level,
            knowledge_area=knowledge_area or self.knowledge_area,
            license=self.license,
            user_created=user,
            public=public,
        )

    def profile_url(self, user):
        return f"/api/v1/authors/{user.user_key}/"

    def learning_objects_url(self, user):
        return f"/api/v1/authors/{user.user_key}/learning-objects/"


class PublicAuthorNotFoundTests(PublicAuthorAPITestBase):
    """Cada causa de "perfil no disponible" responde el mismo 404 en ambos endpoints."""

    def assert_not_found_in_both_endpoints(self, user):
        for url in (self.profile_url(user), self.learning_objects_url(user)):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(response.data, {"detail": "Not found."})

    def test_visible_author_is_found(self):
        self.assertEqual(self.client.get(self.profile_url(self.author)).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(self.learning_objects_url(self.author)).status_code, status.HTTP_200_OK)

    def test_unknown_user_key(self):
        unknown = self.user_model(user_key=uuid.uuid4())
        self.assert_not_found_in_both_endpoints(unknown)

    def test_user_without_teacher_profile(self):
        student_user = self.user_model.objects.create_general_user(
            email="student-author@example.com", first_name="Ana", last_name="Lopez", password="StrongPass123"
        )
        student_user.student = Student.objects.create(has_disability=False, is_active=True, is_account_active=True)
        student_user.save()
        self.create_learning_object(student_user, public=True)

        self.assert_not_found_in_both_endpoints(student_user)

    def test_inactive_teacher(self):
        self.author.teacher.is_active = False
        self.author.teacher.save()

        self.assert_not_found_in_both_endpoints(self.author)

    def test_profile_disabled_by_teacher(self):
        PublicProfile.objects.create(user=self.author, is_public=False)

        self.assert_not_found_in_both_endpoints(self.author)

    def test_teacher_without_public_learning_objects(self):
        teacher = self.create_teacher("private-only@example.com")
        self.create_learning_object(teacher, public=False)

        self.assert_not_found_in_both_endpoints(teacher)

    def test_invalid_user_key_format_returns_404(self):
        response = self.client.get("/api/v1/authors/123/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PublicAuthorProfileTests(PublicAuthorAPITestBase):
    """Valida el contenido del perfil público."""

    def test_fixed_fields_without_saved_profile(self):
        """Sin fila de `PublicProfile` salen los datos de la cuenta y nada opcional."""
        profession = Profession.objects.create(description="Ingeniero Civil")
        self.author.teacher.professions.add(profession)
        # Un OA privado no debe aportar su área de conocimiento.
        private_area = KnowledgeArea.objects.create(
            name_es="Privada", description_es="Desc", name_en="Private", description_en="Desc"
        )
        self.create_learning_object(self.author, public=False, knowledge_area=private_area)
        # Otro OA público de la misma área no la repite.
        self.create_learning_object(self.author, public=True)

        response = self.client.get(self.profile_url(self.author))

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["user_key"], str(self.author.user_key))
        self.assertEqual(response.data["email"], self.author.email)
        self.assertNotIn("id", response.data)
        self.assertEqual(response.data["professions"], [{"id": profession.id, "description": "Ingeniero Civil"}])
        self.assertEqual(
            response.data["knowledge_areas"],
            [{"id": self.knowledge_area.id, "name_es": "Ingeniería", "name_en": "Engineering"}],
        )
        self.assertEqual(response.data["member_since"], self.author.created.year)
        self.assertEqual(response.data["links"], [])
        self.assertEqual(response.data["degrees"], [])
        for optional_field in PublicProfile.VISIBILITY_DEFAULTS:
            self.assertNotIn(optional_field, response.data)
        self.assertNotIn("highest_degree", response.data)

    def test_optional_fields_follow_visibility_and_skip_empty(self):
        PublicProfile.objects.create(
            user=self.author,
            headline="Docente de Ingenieria Civil",
            research_group="GIIT",
            bio="",
            research_lines=["Hidraulica"],
            subjects=[],
            field_visibility={"research_group": "private"},
        )

        response = self.client.get(self.profile_url(self.author))

        self.assertEqual(response.data["headline"], "Docente de Ingenieria Civil")
        self.assertEqual(response.data["research_lines"], ["Hidraulica"])
        # "Solo yo": no viene aunque tenga valor.
        self.assertNotIn("research_group", response.data)
        # Vacíos: no vienen aunque estén en "Público".
        self.assertNotIn("bio", response.data)
        self.assertNotIn("subjects", response.data)

    def test_location_is_never_published(self):
        self.author.country_code = "EC"
        self.author.country_name = "Ecuador"
        self.author.province_code = "A"
        self.author.province_name = "Azuay"
        self.author.city_name = "Cuenca"
        self.author.university_name = "Universidad Politecnica Salesiana"
        self.author.save()
        profile = PublicProfile.objects.create(user=self.author)

        response = self.client.get(self.profile_url(self.author))
        self.assertNotIn("location", response.data)
        # Solo la universidad; ni pais, ni provincia, ni ciudad.
        self.assertEqual(response.data["university_name"], "Universidad Politecnica Salesiana")
        for field in ("country_code", "country_name", "province_code", "province_name", "city_name", "campus"):
            self.assertNotIn(field, response.data)

        # Aunque un perfil antiguo la tenga marcada como pública.
        profile.field_visibility = {"location": "public"}
        profile.save()
        response = self.client.get(self.profile_url(self.author))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("location", response.data)

    def test_only_visible_links_and_degrees(self):
        profile = PublicProfile.objects.create(user=self.author)
        UserLink.objects.create(profile=profile, type="orcid", url="https://orcid.org/0000-0002-1825-0097", order=1)
        UserLink.objects.create(profile=profile, type="linkedin", url="https://linkedin.com/in/juan", is_visible=False)
        AcademicDegree.objects.create(profile=profile, level="phd", title="Doctor", institution="UPM", is_visible=False)
        AcademicDegree.objects.create(profile=profile, level="master", title="Magister", institution="UPS", year=2015)

        response = self.client.get(self.profile_url(self.author))

        self.assertEqual(response.data["links"], [{"type": "orcid", "url": "https://orcid.org/0000-0002-1825-0097"}])
        self.assertEqual(
            response.data["degrees"],
            [{"level": "master", "title": "Magister", "institution": "UPS", "year": 2015}],
        )
        # El PhD oculto no cuenta para el grado más alto público.
        self.assertEqual(response.data["highest_degree"], "master")

    def test_query_count_does_not_grow_with_profile_data(self):
        """Links, títulos, profesiones y OA se cargan en bloque, no uno por uno."""
        profile = PublicProfile.objects.create(user=self.author)

        def count_queries():
            with CaptureQueriesContext(connection) as context:
                response = self.client.get(self.profile_url(self.author))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return len(context.captured_queries)

        baseline = count_queries()

        for index, link_type in enumerate(("orcid", "linkedin", "website")):
            url = {
                "orcid": "https://orcid.org/0000-0002-1825-0097",
                "linkedin": "https://linkedin.com/in/juan",
                "website": "https://juan.dev",
            }[link_type]
            UserLink.objects.create(profile=profile, type=link_type, url=url, order=index)
            AcademicDegree.objects.create(profile=profile, level="master", title=f"T{index}", institution="UPS")
            self.author.teacher.professions.add(Profession.objects.create(description=f"Profesion {index}"))
            self.create_learning_object(self.author, public=True)

        self.assertEqual(count_queries(), baseline)


class PublicAuthorLearningObjectsTests(PublicAuthorAPITestBase):
    """Valida la grilla de OA del perfil y sus totales por OA."""

    def test_lists_only_public_learning_objects_of_the_author(self):
        self.create_learning_object(self.author, public=False)
        other_teacher = self.create_teacher("other-author@example.com")
        self.create_learning_object(other_teacher, public=True)

        response = self.client.get(self.learning_objects_url(self.author))

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(set(response.data), {"count", "links", "pages", "results"})
        item = response.data["results"][0]
        self.assertEqual(item["id"], self.public_oa.id)
        # Mismo formato que las cards: `user_created` mantiene email y suma `user_key`.
        self.assertEqual(item["user_created"]["email"], self.author.email)
        self.assertEqual(item["user_created"]["user_key"], str(self.author.user_key))

    def test_page_size_is_10_by_default_and_can_be_chosen(self):
        for _ in range(24):
            self.create_learning_object(self.author, public=True)
        # 25 OA publicos en total (24 + `public_oa`).
        url = self.learning_objects_url(self.author)

        response = self.client.get(url)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["pages"], 3)

        response = self.client.get(url, {"page_size": 20, "page": 2})
        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(response.data["pages"], 2)

    def test_page_size_is_capped_at_50(self):
        for _ in range(54):
            self.create_learning_object(self.author, public=True)

        response = self.client.get(self.learning_objects_url(self.author), {"page_size": 500})

        self.assertEqual(len(response.data["results"]), 50)
        self.assertEqual(response.data["pages"], 2)

    def test_views_and_downloads_are_totals_per_learning_object(self):
        # `ViewInteraction` puede tener varias filas por OA: se suman todas.
        ViewInteraction.objects.create(learning_object=self.public_oa, view=10)
        ViewInteraction.objects.create(learning_object=self.public_oa, view=5)
        # `Interaction` guarda una fila por usuario: se suman todas.
        for index, downloads in enumerate((3, 4)):
            reader = self.user_model.objects.create_general_user(
                email=f"reader-{index}@example.com", first_name="R", last_name="R", password="StrongPass123"
            )
            Interaction.objects.create(learning_object=self.public_oa, user=reader, downloaded=downloads)
        oa_without_interactions = self.create_learning_object(self.author, public=True)

        response = self.client.get(self.learning_objects_url(self.author))

        totals = {item["id"]: (item["views"], item["downloads"]) for item in response.data["results"]}
        self.assertEqual(totals[self.public_oa.id], (15, 7))
        self.assertEqual(totals[oa_without_interactions.id], (0, 0))
