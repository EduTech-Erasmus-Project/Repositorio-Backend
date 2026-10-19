"""Pruebas del comando `normalize_user_location`.

El comando ajusta pais, provincia y ciudad de los usuarios al catalogo de
`@countrystatecity/countries-browser`. Aqui se reemplaza la descarga desde
jsDelivr por un catalogo en memoria con el mismo formato de archivos.
"""

from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from applications.user.management.commands.normalize_user_location import Command


class FakeCatalog:
    """Catalogo en memoria con la misma interfaz que `CountryStateCityCatalog`."""

    FILES = {
        "countries.json": [
            {"iso2": "EC", "name": "Ecuador", "native": "Ecuador"},
            {"iso2": "ES", "name": "Spain", "native": "España"},
            {"iso2": "US", "name": "United States", "native": "United States"},
        ],
        "country/EC.json": {"iso2": "EC", "name": "Ecuador", "translations": {"es": "Ecuador"}},
        "country/ES.json": {"iso2": "ES", "name": "Spain", "translations": {"es": "España"}},
        "country/US.json": {"iso2": "US", "name": "United States", "translations": {"es": "Estados Unidos"}},
        "states/EC.json": [
            {"iso2": "A", "name": "Azuay", "native": "Azuay"},
            {"iso2": "P", "name": "Pichincha", "native": "Pichincha"},
        ],
        "cities/EC-A.json": [{"name": "Cuenca", "native": "Cuenca"}],
        "cities/EC-P.json": [{"name": "Quito", "native": "Quito"}, {"name": "Sangolquí", "native": "Sangolquí"}],
        "states/ES.json": [{"iso2": "M", "name": "Madrid", "native": "Madrid"}],
        "cities/ES-M.json": [{"name": "Madrid", "native": "Madrid"}],
    }

    def countries(self):
        return self.FILES["countries.json"]

    def country_detail(self, iso2):
        return self.FILES.get(f"country/{iso2}.json", {})

    def states(self, iso2):
        return self.FILES.get(f"states/{iso2}.json", [])

    def cities(self, country_iso2, state_iso2):
        return self.FILES.get(f"cities/{country_iso2}-{state_iso2}.json", [])


@mock.patch.object(Command, "get_catalog", lambda self, version: FakeCatalog())
class NormalizeUserLocationCommandTests(TestCase):
    """Normaliza la ubicacion copiada desde los catalogos antiguos."""

    def setUp(self):
        self.user_model = get_user_model()
        self._sequence = 0

    def _user(self, **location):
        self._sequence += 1
        user = self.user_model.objects.create_general_user(
            email=f"location-{self._sequence}@example.com",
            first_name="Usuario",
            last_name="Ubicacion",
            password="StrongPass123",
        )
        self.user_model.objects.filter(pk=user.pk).update(**location)
        user.refresh_from_db()
        return user

    def _run(self, *args):
        out = StringIO()
        call_command("normalize_user_location", *args, stdout=out)
        return out.getvalue()

    def test_names_are_matched_ignoring_case_and_accents(self):
        user = self._user(
            country_code="EC", country_name="ECUADOR",
            province_name="pichincha", city_name="sangolqui", university_name="ESPE",
        )

        self._run()

        user.refresh_from_db()
        self.assertEqual(user.country_name, "Ecuador")
        self.assertEqual(user.province_code, "P")
        self.assertEqual(user.province_name, "Pichincha")
        self.assertEqual(user.city_name, "Sangolquí")
        self.assertEqual(user.university_name, "ESPE")

    def test_country_name_is_saved_in_spanish(self):
        by_code = self._user(country_code="ES", country_name="Spain", city_name="Madrid")
        by_spanish_name = self._user(country_name="Estados Unidos")

        self._run()

        by_code.refresh_from_db()
        by_spanish_name.refresh_from_db()
        self.assertEqual(by_code.country_name, "España")
        self.assertEqual(by_spanish_name.country_code, "US")
        self.assertEqual(by_spanish_name.country_name, "Estados Unidos")

    def test_province_is_deduced_from_city(self):
        user = self._user(country_code="EC", country_name="Ecuador", city_name="Cuenca")

        self._run()

        user.refresh_from_db()
        self.assertEqual(user.province_code, "A")
        self.assertEqual(user.province_name, "Azuay")

    def test_values_not_in_catalog_are_kept_and_reported(self):
        user = self._user(
            country_code="EC", country_name="Ecuador",
            province_name="Pichincha", city_name="Rumiñahui",
        )
        unknown_country = self._user(country_name="Atlantida", city_name="Poseidonia")

        output = self._run()

        user.refresh_from_db()
        unknown_country.refresh_from_db()
        self.assertEqual(user.city_name, "Rumiñahui")
        self.assertEqual(user.province_code, "P")
        self.assertEqual(unknown_country.country_name, "Atlantida")
        self.assertEqual(unknown_country.country_code, "")
        self.assertIn("ciudad 'Rumiñahui'", output)
        self.assertIn("pais 'Atlantida'", output)

    def test_dry_run_does_not_write(self):
        user = self._user(country_code="EC", country_name="ecuador", city_name="quito")

        output = self._run("--dry-run")

        user.refresh_from_db()
        self.assertEqual(user.country_name, "ecuador")
        self.assertEqual(user.city_name, "quito")
        self.assertIn("Would update 1 user location(s).", output)

    def test_users_without_location_are_skipped(self):
        self._user()

        output = self._run()

        self.assertIn("Updated 0 user location(s).", output)
