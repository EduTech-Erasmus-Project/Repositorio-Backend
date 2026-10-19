"""Pruebas de la ubicacion del usuario guardada como texto.

La ubicacion (pais, provincia, ciudad y universidad) dejo de depender de los
catalogos `address`; el frontend la toma de un catalogo geografico externo y
el backend la guarda como codigos ISO y nombres. Esta suite cubre:

- registro de docentes y expertos con la ubicacion exigida
- respuesta del API con los campos de texto
- filtros del reporte administrativo por pais, provincia, ciudad y universidad
- copia de datos de la migracion `user.0006_user_location_text`
"""

import importlib
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from applications.profession.models import Profession
from applications.user.models import Administrator, Teacher
from applications.user.views import ManagementUserView, ReportListAPIView


REGISTER_URL = "/api/v1/user-management/"

LOCATION = {
    "country_code": "ec",
    "country_name": "Ecuador",
    "province_code": "P",
    "province_name": "Pichincha",
    "city_name": "Quito",
    "university_name": "Universidad Politécnica Salesiana",
}


@mock.patch.object(ManagementUserView, "set_email_conform", lambda *args, **kwargs: None)
@mock.patch.object(ManagementUserView, "checkEmail", lambda *args, **kwargs: True)
class UserLocationRegistrationTests(TestCase):
    """Registro de docentes y expertos con ubicacion como texto."""

    def setUp(self):
        self.client = APIClient()
        self.profession = Profession.objects.create(description="Docente Location")

    def _teacher_payload(self, **overrides):
        payload = {
            "roles": ["teacher"],
            "first_name": "Ana",
            "last_name": "Docente",
            "email": "ana.docente@example.com",
            "password": "StrongPass123",
            "professions": [self.profession.id],
            **LOCATION,
        }
        payload.update(overrides)
        return payload

    def test_teacher_registration_saves_location_as_text(self):
        """El alta de docente guarda la ubicacion y la devuelve en la respuesta."""
        response = self.client.post(REGISTER_URL, self._teacher_payload(), format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user = get_user_model().objects.get(email="ana.docente@example.com")
        self.assertEqual(user.country_code, "EC")
        self.assertEqual(user.country_name, "Ecuador")
        self.assertEqual(user.province_code, "P")
        self.assertEqual(user.province_name, "Pichincha")
        self.assertEqual(user.city_name, "Quito")
        self.assertEqual(user.university_name, "Universidad Politécnica Salesiana")

        self.assertEqual(response.data["country_code"], "EC")
        self.assertEqual(response.data["city_name"], "Quito")
        self.assertNotIn("campus", response.data)
        self.assertNotIn("city", response.data)

    def test_expert_registration_saves_location_as_text(self):
        """El alta de experto tambien guarda la ubicacion."""
        payload = {
            "roles": ["expert"],
            "first_name": "Luis",
            "last_name": "Experto",
            "email": "luis.experto@example.com",
            "password": "StrongPass123",
            "expert_level": "Alto",
            **LOCATION,
        }

        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user = get_user_model().objects.get(email="luis.experto@example.com")
        self.assertEqual(user.country_code, "EC")
        self.assertEqual(user.university_name, "Universidad Politécnica Salesiana")

    def test_teacher_registration_requires_location(self):
        """Pais, ciudad y universidad son obligatorios para docentes."""
        payload = self._teacher_payload(country_code="", city_name="", university_name="")
        payload.pop("country_name")

        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, 400, response.data)
        for field in ("country_code", "country_name", "city_name", "university_name"):
            self.assertIn(field, response.data)
        self.assertFalse(get_user_model().objects.filter(email="ana.docente@example.com").exists())
        self.assertFalse(Teacher.objects.exists())

    def test_teacher_registration_allows_missing_province(self):
        """La provincia es opcional porque algunos paises no la tienen en el catalogo."""
        payload = self._teacher_payload()
        payload.pop("province_code")
        payload.pop("province_name")

        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user = get_user_model().objects.get(email="ana.docente@example.com")
        self.assertEqual(user.province_code, "")
        self.assertEqual(user.province_name, "")

    def test_teacher_registration_rejects_invalid_country_code(self):
        """El codigo de pais debe ser ISO de 2 letras."""
        response = self.client.post(REGISTER_URL, self._teacher_payload(country_code="ECU"), format="json")

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("country_code", response.data)


class UserLocationReportFilterTests(TestCase):
    """Filtros de texto del reporte administrativo de docentes."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user_model = get_user_model()
        administrator = Administrator.objects.create(
            country="EC", city="Quito", phone=999999999, observation="Admin", is_active=True,
        )
        self.admin_user = self.user_model.objects.create_admin_user(
            email="admin-location@example.com",
            first_name="Admin",
            last_name="Location",
            password="StrongPass123",
        )
        self.admin_user.administrator = administrator
        self.admin_user.save()

        self.quito = self._create_teacher("quito", "EC", "Pichincha", "Quito", "Universidad Politécnica Salesiana")
        self.cuenca = self._create_teacher("cuenca", "EC", "Azuay", "Cuenca", "Universidad de Cuenca")
        self.bogota = self._create_teacher("bogota", "CO", "Bogotá D.C.", "Bogotá", "Universidad Nacional")

    def _create_teacher(self, slug, country_code, province_name, city_name, university_name):
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=f"{slug}@example.com",
            first_name="Teacher",
            last_name=slug.title(),
            password="StrongPass123",
        )
        user.teacher = teacher
        user.country_code = country_code
        user.province_name = province_name
        user.city_name = city_name
        user.university_name = university_name
        user.save()
        return user

    def _report_emails(self, params):
        request = self.factory.get("/api/v1/report", params)
        force_authenticate(request, user=self.admin_user)
        response = ReportListAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200, response.data)
        return {row["email"] for row in response.data["results"]}

    def test_filter_by_country_code_is_case_insensitive(self):
        self.assertEqual(
            self._report_emails({"country": "ec"}),
            {self.quito.email, self.cuenca.email},
        )

    def test_filter_by_province_city_and_university_is_partial(self):
        self.assertEqual(self._report_emails({"province": "azu"}), {self.cuenca.email})
        self.assertEqual(self._report_emails({"city": "bogo"}), {self.bogota.email})
        self.assertEqual(self._report_emails({"university": "salesiana"}), {self.quito.email})

    def test_report_rows_include_location_fields(self):
        request = self.factory.get("/api/v1/report", {"city": "Quito"})
        force_authenticate(request, user=self.admin_user)
        response = ReportListAPIView.as_view()(request)

        row = response.data["results"][0]
        self.assertEqual(row["country_code"], "EC")
        self.assertEqual(row["province_name"], "Pichincha")
        self.assertEqual(row["university_name"], "Universidad Politécnica Salesiana")
        self.assertNotIn("campus", row)


class UserLocationDataMigrationTests(SimpleTestCase):
    """Copia de la ubicacion desde los catalogos a texto en la migracion 0006."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.migration = importlib.import_module("applications.user.migrations.0006_user_location_text")

    @staticmethod
    def _catalog_user(country=None, province=None, city=None, university=None, campus=None):
        return SimpleNamespace(
            country=country, province=province, city=city, university=university, campus=campus,
        )

    def test_country_code_is_resolved_ignoring_case_and_accents(self):
        self.assertEqual(self.migration.country_code_for("Ecuador"), "EC")
        self.assertEqual(self.migration.country_code_for("  perú "), "PE")
        self.assertEqual(self.migration.country_code_for("ESPAÑA"), "ES")
        self.assertEqual(self.migration.country_code_for("Estados Unidos"), "US")
        self.assertEqual(self.migration.country_code_for("Pais inventado"), "")
        self.assertEqual(self.migration.country_code_for(None), "")

    def test_full_location_is_copied(self):
        country = SimpleNamespace(name="Ecuador")
        province = SimpleNamespace(name="Pichincha", country=country)
        city = SimpleNamespace(name="Quito", province=province)
        user = self._catalog_user(
            country=country, province=province, city=city,
            university=SimpleNamespace(name="UPS"),
        )

        self.assertEqual(
            self.migration.location_values_for(user),
            {
                "country_code": "EC",
                "country_name": "Ecuador",
                "province_name": "Pichincha",
                "city_name": "Quito",
                "university_name": "UPS",
            },
        )

    def test_country_and_province_are_derived_from_city_or_campus(self):
        country = SimpleNamespace(name="Colombia")
        province = SimpleNamespace(name="Antioquia", country=country)
        city = SimpleNamespace(name="Medellín", province=province)

        from_city = self.migration.location_values_for(self._catalog_user(city=city))
        from_campus = self.migration.location_values_for(
            self._catalog_user(campus=SimpleNamespace(city=city))
        )

        for values in (from_city, from_campus):
            self.assertEqual(values["country_code"], "CO")
            self.assertEqual(values["country_name"], "Colombia")
            self.assertEqual(values["province_name"], "Antioquia")
            self.assertEqual(values["city_name"], "Medellín")

    def test_user_without_location_gets_empty_values(self):
        values = self.migration.location_values_for(self._catalog_user())

        self.assertFalse(any(values.values()))
