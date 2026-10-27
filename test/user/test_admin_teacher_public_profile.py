"""Pruebas del perfil público dentro del detalle administrativo del docente.

Cubre:
- `public_profile` es `null` si el docente nunca guardó su perfil
- con perfil, viene completo (también lo oculto) con el formato del perfil propio
- ambas rutas (`teacher-to-approve` y `teacher-to-disapproved`)
- el listado administrativo no cambia
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from applications.user.models import (
    AcademicDegree,
    Administrator,
    PublicProfile,
    Teacher,
    UserLink,
)


ORCID_URL = "https://orcid.org/0000-0002-1825-0097"


class AdminTeacherPublicProfileTests(TestCase):
    """Valida `public_profile` en `teacher-to-approve/<id>` y `teacher-to-disapproved/<id>`."""

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_admin_user(
            email="admin-profile@example.com",
            first_name="Admin",
            last_name="Perfil",
            password="StrongPass123",
        )
        self.admin_user.administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin perfil público",
            is_active=True,
        )
        self.admin_user.save()

        self.teacher_user = self.user_model.objects.create_general_user(
            email="teacher-admin-profile@example.com",
            first_name="Juan",
            last_name="Perez",
            password="StrongPass123",
        )
        self.teacher_user.teacher = Teacher.objects.create(is_active=False, is_account_active=True)
        self.teacher_user.save()

        self.client.force_authenticate(self.admin_user)

    def detail_url(self, prefix="teacher-to-approve"):
        return f"/api/v1/{prefix}/{self.teacher_user.id}/"

    def create_profile(self):
        profile = PublicProfile.objects.create(
            user=self.teacher_user,
            headline="Docente de Ingeniería",
            bio="Bio oculta",
            field_visibility={"bio": PublicProfile.VISIBILITY_PRIVATE},
            is_public=False,
        )
        UserLink.objects.create(profile=profile, type="orcid", url=ORCID_URL, is_visible=False)
        AcademicDegree.objects.create(
            profile=profile,
            level="phd",
            title="Doctorado en Computación",
            institution="UPS",
            year=2020,
            is_visible=False,
        )
        return profile

    def test_public_profile_is_null_without_saved_profile(self):
        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["public_profile"])

    def test_public_profile_includes_hidden_data(self):
        self.create_profile()

        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = response.data["public_profile"]
        self.assertEqual(profile["user_key"], str(self.teacher_user.user_key))
        self.assertFalse(profile["is_public"])
        self.assertEqual(profile["bio"], "Bio oculta")
        self.assertEqual(profile["field_visibility"]["bio"], PublicProfile.VISIBILITY_PRIVATE)
        self.assertNotIn("location", profile["field_visibility"])
        self.assertEqual(profile["highest_degree"], "phd")
        self.assertEqual(len(profile["links"]), 1)
        self.assertFalse(profile["links"][0]["is_visible"])
        self.assertEqual(len(profile["degrees"]), 1)
        self.assertFalse(profile["degrees"][0]["is_visible"])

    def test_public_profile_matches_own_profile_format(self):
        self.create_profile()

        admin_response = self.client.get(self.detail_url())
        self.teacher_user.teacher.is_active = True
        self.teacher_user.teacher.save()
        self.client.force_authenticate(self.teacher_user)
        own_response = self.client.get("/api/v1/user/public-profile/")

        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_response.data["public_profile"], own_response.data)

    def test_disapproved_route_also_includes_public_profile(self):
        self.create_profile()

        response = self.client.get(self.detail_url("teacher-to-disapproved"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["public_profile"]["headline"], "Docente de Ingeniería")

    def test_existing_fields_are_kept(self):
        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.teacher_user.id)
        self.assertEqual(response.data["email"], self.teacher_user.email)
        self.assertEqual(response.data["rol_solicitados"], ["teacher"])

    def test_list_does_not_include_public_profile(self):
        self.create_profile()

        response = self.client.get("/api/v1/teacher-to-approve/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertNotIn("public_profile", response.data["results"][0])

    def test_detail_requires_administrator(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get(self.detail_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
