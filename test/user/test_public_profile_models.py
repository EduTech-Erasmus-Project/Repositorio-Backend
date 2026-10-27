"""Pruebas de los modelos del perfil público del autor.

Cubre las reglas que viven en el modelo y que después usan los serializers:
- visibilidad por campo con valores por defecto
- grado académico más alto calculado desde los títulos
- un enlace por tipo en cada perfil
- `user_key` expuesto en `UserCommentSerializer` sin perder campos existentes
"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from applications.user.models import AcademicDegree, PublicProfile, Teacher, UserLink
from applications.user.serializers import UserCommentSerializer


class PublicProfileTestMixin:
    """Crea un docente con perfil público vacío para cada prueba."""

    def setUp(self):
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        self.user = get_user_model().objects.create_general_user(
            email="public-profile@example.com",
            first_name="Juan",
            last_name="Perez",
            password="StrongPass123",
        )
        self.user.teacher = teacher
        self.user.save()
        self.profile = PublicProfile.objects.create(user=self.user)


class PublicProfileVisibilityTests(PublicProfileTestMixin, TestCase):
    """Valida la combinación de visibilidad guardada con los valores por defecto."""

    def test_without_stored_visibility_uses_defaults(self):
        """Sin nada guardado, todos los campos son públicos."""
        visibility = self.profile.get_field_visibility()

        self.assertEqual(visibility, PublicProfile.VISIBILITY_DEFAULTS)
        self.assertNotIn("location", visibility)

    def test_stored_visibility_overrides_defaults(self):
        """Lo guardado reemplaza solo las claves indicadas."""
        self.profile.field_visibility = {"bio": "private"}

        visibility = self.profile.get_field_visibility()

        self.assertEqual(visibility["bio"], "private")
        self.assertEqual(visibility["headline"], "public")

    def test_invalid_keys_and_values_are_ignored(self):
        """Claves desconocidas o valores fuera de la lista no alteran el resultado."""
        # `location` ya no es configurable: guardada en la base se ignora.
        self.profile.field_visibility = {"email": "public", "bio": "everyone", "location": "public"}

        visibility = self.profile.get_field_visibility()

        self.assertEqual(visibility, PublicProfile.VISIBILITY_DEFAULTS)

    def test_is_field_public(self):
        """`is_field_public` respeta la visibilidad combinada."""
        self.profile.field_visibility = {"research_group": "private"}

        self.assertTrue(self.profile.is_field_public("headline"))
        self.assertFalse(self.profile.is_field_public("research_group"))
        self.assertFalse(self.profile.is_field_public("location"))


class PublicProfileHighestDegreeTests(PublicProfileTestMixin, TestCase):
    """Valida que el grado más alto se calcule desde `AcademicDegree`."""

    def create_degree(self, level, year, is_visible=True):
        return AcademicDegree.objects.create(
            profile=self.profile,
            level=level,
            title=f"Titulo {level}",
            institution="UPS",
            year=year,
            is_visible=is_visible,
        )

    def test_without_degrees_returns_none(self):
        self.assertIsNone(self.profile.get_highest_degree())

    def test_returns_highest_rank_not_most_recent(self):
        """El rango decide, no el año: un PhD antiguo gana a una maestría reciente."""
        self.create_degree("phd", 2010)
        self.create_degree("master", 2022)
        self.create_degree("third", 2005)

        self.assertEqual(self.profile.get_highest_degree(), "phd")

    def test_rank_covers_all_levels(self):
        """Especialización queda entre tercer nivel y maestría; técnico es el más bajo."""
        self.create_degree("technical", 2005)
        self.assertEqual(self.profile.get_highest_degree(), "technical")

        self.create_degree("third", 2008)
        self.assertEqual(self.profile.get_highest_degree(), "third")

        self.create_degree("specialty", 2011)
        self.assertEqual(self.profile.get_highest_degree(), "specialty")

        self.create_degree("master", 2014)
        self.assertEqual(self.profile.get_highest_degree(), "master")

    def test_hidden_degrees_are_ignored_by_default(self):
        """En el perfil público solo cuentan los títulos visibles."""
        self.create_degree("phd", 2019, is_visible=False)
        self.create_degree("master", 2015)

        self.assertEqual(self.profile.get_highest_degree(), "master")

    def test_include_hidden_degrees_for_owner(self):
        """En el perfil propio se consideran también los títulos ocultos."""
        self.create_degree("phd", 2019, is_visible=False)
        self.create_degree("master", 2015)

        self.assertEqual(self.profile.get_highest_degree(only_visible=False), "phd")

    def test_only_hidden_degrees_returns_none(self):
        self.create_degree("phd", 2019, is_visible=False)

        self.assertIsNone(self.profile.get_highest_degree())


class UserLinkConstraintTests(PublicProfileTestMixin, TestCase):
    """Valida la restricción de un enlace por tipo en cada perfil."""

    def test_duplicate_link_type_in_same_profile_fails(self):
        UserLink.objects.create(profile=self.profile, type="orcid", url="https://orcid.org/0000-0002-1825-0097")

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserLink.objects.create(profile=self.profile, type="orcid", url="https://orcid.org/0000-0001-0000-0000")

    def test_same_link_type_in_different_profiles_is_allowed(self):
        other_user = get_user_model().objects.create_general_user(
            email="other-profile@example.com",
            first_name="Ana",
            last_name="Lopez",
            password="StrongPass123",
        )
        other_profile = PublicProfile.objects.create(user=other_user)

        UserLink.objects.create(profile=self.profile, type="orcid", url="https://orcid.org/0000-0002-1825-0097")
        UserLink.objects.create(profile=other_profile, type="orcid", url="https://orcid.org/0000-0001-0000-0000")

        self.assertEqual(UserLink.objects.filter(type="orcid").count(), 2)

    def test_deleting_user_deletes_profile_links_and_degrees(self):
        """El perfil y sus filas dependen de la cuenta."""
        UserLink.objects.create(profile=self.profile, type="orcid", url="https://orcid.org/0000-0002-1825-0097")
        AcademicDegree.objects.create(profile=self.profile, level="phd", title="Doctor", institution="UPM")

        self.user.delete()

        self.assertFalse(PublicProfile.objects.exists())
        self.assertFalse(UserLink.objects.exists())
        self.assertFalse(AcademicDegree.objects.exists())


class UserCommentSerializerTests(PublicProfileTestMixin, TestCase):
    """Valida que `user_created` agregue `user_key` sin perder campos."""

    def test_includes_user_key_and_keeps_existing_fields(self):
        data = UserCommentSerializer(self.user).data

        self.assertEqual(
            set(data.keys()),
            {"id", "user_key", "first_name", "last_name", "image_url", "email"},
        )
        self.assertEqual(data["user_key"], str(self.user.user_key))
        self.assertEqual(data["email"], self.user.email)
