"""Pruebas del paso del catálogo de niveles a la CINE 2011.

Cubren el comando `apply_isced_levels` (renombra sin cambiar ids, crea los
niveles que faltan, se puede repetir) y que el listado público salga en el
orden CINE aunque los ids no lo sigan.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel


class ApplyIscedLevelsCommandTests(TestCase):
    """El catálogo anterior de 5 niveles pasa a los 9 niveles CINE."""

    def setUp(self):
        old_levels = [
            ("Educación primaria", "Elementary School"),
            ("Educación secundaria", "Secondary School"),
            ("Escuela intermedia", "Middle School"),
            ("División superior universitaria", "University"),
            ("Profesional", "Professional"),
        ]
        self.old = {
            name_es: EducationLevel.objects.create(name_es=name_es, name_en=name_en)
            for name_es, name_en in old_levels
        }

    def _run(self, *args):
        out = StringIO()
        call_command("apply_isced_levels", *args, stdout=out)
        return out.getvalue()

    def test_renames_existing_levels_keeping_their_ids(self):
        self._run()

        expected = {
            "Educación primaria": 1,
            "Escuela intermedia": 2,
            "Educación secundaria": 3,
            "División superior universitaria": 6,
            "Profesional": 7,
        }
        for old_name, code in expected.items():
            level = EducationLevel.objects.get(pk=self.old[old_name].pk)
            self.assertEqual(level.isced_code, code)
            self.assertTrue(level.name_es.startswith(f"CINE {code} - "))
            self.assertTrue(level.name_en.startswith(f"ISCED {code} - "))

        self.assertEqual(
            EducationLevel.objects.get(isced_code=3).name_es,
            "CINE 3 - Educación secundaria alta",
        )

    def test_creates_missing_levels_with_typical_ages(self):
        self._run()

        self.assertEqual(EducationLevel.objects.count(), 9)
        self.assertEqual(
            sorted(EducationLevel.objects.values_list("isced_code", flat=True)),
            list(range(9)),
        )
        early = EducationLevel.objects.get(isced_code=0)
        self.assertEqual((early.typical_age_min, early.typical_age_max), (0, 5))
        doctoral = EducationLevel.objects.get(isced_code=8)
        self.assertEqual((doctoral.typical_age_min, doctoral.typical_age_max), (24, None))

    def test_can_run_twice_without_duplicates(self):
        self._run()
        self._run()

        self.assertEqual(EducationLevel.objects.count(), 9)

    def test_dry_run_changes_nothing(self):
        output = self._run("--dry-run")

        self.assertIn("crear", output)
        self.assertEqual(EducationLevel.objects.count(), 5)
        self.assertFalse(EducationLevel.objects.filter(isced_code__isnull=False).exists())


class EducationLevelIscedOrderTests(TestCase):
    """El listado sale por código CINE, no por id."""

    def setUp(self):
        EducationLevel.objects.create(name_es="CINE 3 - Alta", name_en="ISCED 3 - Upper", isced_code=3)
        EducationLevel.objects.create(name_es="Sin código", name_en="No code")
        EducationLevel.objects.create(name_es="CINE 1 - Primaria", name_en="ISCED 1 - Primary", isced_code=1)
        EducationLevel.objects.create(name_es="CINE 2 - Baja", name_en="ISCED 2 - Lower", isced_code=2)

    def test_public_list_is_ordered_by_isced_code_with_uncoded_last(self):
        response = APIClient().get("/api/v1/education-level/", HTTP_ACCEPT_LANGUAGE="es")

        self.assertEqual(response.status_code, 200, response.data)
        names = [item["name"] for item in response.data["values"]]
        self.assertEqual(
            names,
            ["CINE 1 - Primaria", "CINE 2 - Baja", "CINE 3 - Alta", "Sin código"],
        )
        self.assertEqual(response.data["values"][0]["isced_code"], 1)
