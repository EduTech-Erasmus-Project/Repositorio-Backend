"""Pruebas del endpoint del perfil público propio (`/api/v1/user/public-profile/`).

Cubre:
- permisos: solo docentes activos
- lectura con y sin fila guardada
- guardado atómico con reemplazo de `links` y `degrees`
- mezcla de `field_visibility`
- validaciones y formato de errores por posición en las listas
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from applications.user.models import (
    AcademicDegree,
    CollaboratingExpert,
    PublicProfile,
    Student,
    Teacher,
    UserLink,
)


ORCID_URL = "https://orcid.org/0000-0002-1825-0097"


class OwnPublicProfileAPITests(TestCase):
    """Valida el contrato del perfil público propio."""

    url = "/api/v1/user/public-profile/"

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.teacher_user = self.create_user("teacher-profile@example.com")
        self.teacher_user.teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        self.teacher_user.save()

    def create_user(self, email):
        return self.user_model.objects.create_general_user(
            email=email,
            first_name="Juan",
            last_name="Perez",
            password="StrongPass123",
        )

    def put(self, payload, user=None):
        self.client.force_authenticate(user or self.teacher_user)
        return self.client.put(self.url, payload, format="json")

    def patch(self, payload):
        self.client.force_authenticate(self.teacher_user)
        return self.client.patch(self.url, payload, format="json")

    # Permisos

    def test_anonymous_user_gets_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_gets_403(self):
        student_user = self.create_user("student-profile@example.com")
        student_user.student = Student.objects.create(
            birthday=date(2000, 1, 1), has_disability=False, is_active=True, is_account_active=True
        )
        student_user.save()
        self.client.force_authenticate(student_user)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.put({"headline": "x"}, user=student_user).status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(PublicProfile.objects.exists())

    def test_expert_without_teacher_profile_gets_403(self):
        expert_user = self.create_user("expert-profile@example.com")
        expert_user.collaboratingExpert = CollaboratingExpert.objects.create(
            expert_level="Alto", is_active=True, is_account_active=True
        )
        expert_user.save()
        self.client.force_authenticate(expert_user)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_teacher_gets_403(self):
        self.teacher_user.teacher.is_active = False
        self.teacher_user.teacher.save()
        self.client.force_authenticate(self.teacher_user)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    # Lectura

    def test_get_without_saved_profile_returns_defaults_and_creates_nothing(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["user_key"], str(self.teacher_user.user_key))
        self.assertTrue(response.data["is_public"])
        self.assertEqual(response.data["headline"], "")
        self.assertEqual(response.data["research_lines"], [])
        self.assertEqual(response.data["field_visibility"], PublicProfile.VISIBILITY_DEFAULTS)
        self.assertIsNone(response.data["highest_degree"])
        self.assertEqual(response.data["links"], [])
        self.assertEqual(response.data["degrees"], [])
        self.assertFalse(PublicProfile.objects.exists())

    def test_get_returns_private_fields_and_hidden_items(self):
        """El perfil propio devuelve todo, también lo marcado como "Solo yo"."""
        profile = PublicProfile.objects.create(
            user=self.teacher_user, research_group="GIIT", field_visibility={"research_group": "private"}
        )
        UserLink.objects.create(profile=profile, type="orcid", url=ORCID_URL, is_visible=False)
        AcademicDegree.objects.create(profile=profile, level="phd", title="Doctor", institution="UPM", is_visible=False)
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get(self.url)

        self.assertEqual(response.data["research_group"], "GIIT")
        self.assertEqual(response.data["field_visibility"]["research_group"], "private")
        self.assertEqual(len(response.data["links"]), 1)
        self.assertEqual(len(response.data["degrees"]), 1)
        self.assertEqual(response.data["highest_degree"], "phd")

    # Guardado

    def test_put_creates_profile_with_links_and_degrees(self):
        response = self.put({
            "headline": "Docente de Ingenieria Civil",
            "research_lines": ["Hidraulica", "Suelos"],
            "links": [{"type": "orcid", "url": ORCID_URL, "order": 1}],
            "degrees": [
                {"level": "master", "title": "Magister", "institution": "UPS", "year": 2015},
                {"level": "phd", "title": "Doctor", "institution": "UPM", "year": 2019},
            ],
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        profile = PublicProfile.objects.get(user=self.teacher_user)
        self.assertEqual(profile.headline, "Docente de Ingenieria Civil")
        self.assertEqual(profile.links.count(), 1)
        self.assertEqual(profile.degrees.count(), 2)
        self.assertEqual(response.data["highest_degree"], "phd")
        self.assertEqual(response.data["links"][0]["type"], "orcid")
        self.assertEqual([degree["year"] for degree in response.data["degrees"]], [2019, 2015])

    def test_put_accepts_new_levels_and_rejects_unknown_ones(self):
        response = self.put({
            "degrees": [
                {"level": "technical", "title": "Tecnologo en Redes", "institution": "IST"},
                {"level": "specialty", "title": "Especialista en Docencia", "institution": "UPS"},
            ],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["highest_degree"], "specialty")

        # Un diplomado no es titulo de educacion superior.
        response = self.put({"degrees": [{"level": "diploma", "title": "Diplomado", "institution": "UPS"}]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("level", response.data["degrees"][0])

    def test_put_replaces_lists_and_missing_key_keeps_them(self):
        self.put({
            "links": [
                {"type": "orcid", "url": ORCID_URL},
                {"type": "website", "url": "https://juanperez.dev"},
            ],
            "degrees": [{"level": "phd", "title": "Doctor", "institution": "UPM"}],
        })

        # Una lista nueva reemplaza la anterior completa.
        response = self.put({"links": [{"type": "linkedin", "url": "https://ec.linkedin.com/in/juan"}]})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual([link["type"] for link in response.data["links"]], ["linkedin"])
        # `degrees` no vino en el body: no se toca.
        self.assertEqual(len(response.data["degrees"]), 1)

        # Una lista vacía borra todo.
        response = self.put({"degrees": []})
        self.assertEqual(response.data["degrees"], [])
        self.assertEqual(len(response.data["links"]), 1)

    def test_patch_merges_field_visibility(self):
        self.put({"field_visibility": {"bio": "private"}})

        response = self.patch({"field_visibility": {"subjects": "private"}})

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["field_visibility"]["bio"], "private")
        self.assertEqual(response.data["field_visibility"]["subjects"], "private")
        self.assertEqual(response.data["field_visibility"]["headline"], "public")

    def test_location_visibility_is_rejected_and_old_key_is_dropped(self):
        response = self.patch({"field_visibility": {"location": "public"}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Un perfil guardado antes de quitar la ubicación conserva la clave.
        self.put({"headline": "Titular"})
        profile = PublicProfile.objects.get(user=self.teacher_user)
        profile.field_visibility = {"location": "public", "bio": "public"}
        profile.save()

        self.patch({"field_visibility": {"bio": "private"}})
        profile.refresh_from_db()
        self.assertEqual(profile.field_visibility, {"bio": "private"})

    def test_patch_only_updates_sent_fields(self):
        self.put({"headline": "Titular", "bio": "Biografia"})

        response = self.patch({"is_public": False})

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertFalse(response.data["is_public"])
        self.assertEqual(response.data["headline"], "Titular")
        self.assertEqual(response.data["bio"], "Biografia")

    def test_html_is_stripped_from_text_fields(self):
        response = self.put({
            "headline": "<b>Docente</b>",
            "bio": "<script>alert(1)</script>Investigo suelos",
            "research_lines": ["<i>Hidraulica</i>"],
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["headline"], "Docente")
        self.assertNotIn("<", response.data["bio"])
        self.assertEqual(response.data["research_lines"], ["Hidraulica"])

    # Validaciones

    def test_invalid_link_error_is_reported_at_its_position_and_nothing_is_saved(self):
        """Atomicidad: un link inválido impide guardar también el resto."""
        response = self.put({
            "headline": "No debe guardarse",
            "links": [
                {"type": "orcid", "url": ORCID_URL},
                {"type": "linkedin", "url": "https://facebook.com/juan"},
            ],
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["links"][0], {})
        self.assertIn("url", response.data["links"][1])
        self.assertFalse(PublicProfile.objects.exists())

    def test_orcid_ending_in_x_is_accepted_and_saved_uppercase(self):
        response = self.put({"links": [{"type": "orcid", "url": "https://orcid.org/0000-0002-1694-233x"}]})

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["links"][0]["url"], "https://orcid.org/0000-0002-1694-233X")

    def test_orcid_error_messages(self):
        response = self.put({"links": [{"type": "orcid", "url": "https://orcid.org/juan"}]})
        self.assertIn("puede ser X", str(response.data["links"][0]["url"][0]))

        response = self.put({"links": [{"type": "orcid", "url": "https://orcid.org/0000-0002-1825-0098"}]})
        self.assertIn("no es válido", str(response.data["links"][0]["url"][0]))

    def test_link_url_rules(self):
        invalid_links = [
            {"type": "website", "url": "http://juanperez.dev"},
            {"type": "orcid", "url": "https://orcid.org/juan"},
            {"type": "orcid", "url": "https://evil.com/0000-0002-1825-0097"},
            # Dígito de control incorrecto (el válido es 0000-0002-1825-0097).
            {"type": "orcid", "url": "https://orcid.org/0000-0002-1825-0098"},
            # Dos dígitos intercambiados.
            {"type": "orcid", "url": "https://orcid.org/0000-0002-8125-0097"},
            {"type": "scholar", "url": "https://google.com/citations?user=abc"},
            {"type": "linkedin", "url": "https://notlinkedin.com/in/juan"},
        ]
        for link in invalid_links:
            with self.subTest(link=link):
                response = self.put({"links": [link]})
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("url", response.data["links"][0])

        valid_links = [
            {"type": "orcid", "url": "https://orcid.org/0000-0002-1694-233X"},
            {"type": "scholar", "url": "https://scholar.google.es/citations?user=abc"},
            {"type": "linkedin", "url": "https://www.linkedin.com/in/juan"},
            {"type": "institutional", "url": "https://ups.edu.ec/juan"},
        ]
        response = self.put({"links": valid_links})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_duplicate_link_type_is_rejected(self):
        response = self.put({"links": [
            {"type": "orcid", "url": ORCID_URL},
            {"type": "orcid", "url": "https://orcid.org/0000-0001-5109-3700"},
        ]})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["links"], ["Hay más de un enlace del mismo tipo."])

    def test_patch_still_requires_complete_list_items(self):
        """En PATCH un item de la lista sin campos requeridos sigue siendo inválido."""
        response = self.patch({"links": [{"type": "orcid"}]})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data["links"][0])

    def test_degree_year_range(self):
        next_year = timezone.localdate().year + 1
        for year in (1949, next_year):
            with self.subTest(year=year):
                response = self.put({"degrees": [{"level": "phd", "title": "Doctor", "institution": "UPM", "year": year}]})
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("year", response.data["degrees"][0])

    def test_field_visibility_rejects_unknown_fields_and_values(self):
        response = self.put({"field_visibility": {"email": "public"}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("field_visibility", response.data)

        response = self.put({"field_visibility": {"bio": "everyone"}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("field_visibility", response.data)

    def test_list_and_text_limits(self):
        cases = [
            {"research_lines": ["a", "b", "c", "d", "e", "f"]},
            {"research_lines": ["x" * 61]},
            {"subjects": ["x"] * 11},
            {"headline": "x" * 121},
            {"bio": "x" * 601},
        ]
        for payload in cases:
            with self.subTest(field=next(iter(payload))):
                response = self.put(payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(next(iter(payload)), response.data)
