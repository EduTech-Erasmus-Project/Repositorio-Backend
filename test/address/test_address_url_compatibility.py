"""Pruebas de contrato de rutas para `address`.

La limpieza de aliases en `address` dejó solo las rutas canónicas sin slash
final para varios endpoints manuales. Esta suite documenta ese cambio de
contrato y evita que vuelvan a reintroducirse rutas duplicadas que terminan
provocando colisiones en OpenAPI o consumo ambiguo desde frontend.

No se busca probar el CRUD completo del módulo. El foco es más fino:
confirmar que los accesos legacy con slash final, antes tolerados por
compatibilidad, hoy responden 404 de forma explícita.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from applications.address.models import Campus, City, Country, Province, University


class AddressURLCompatibilityTests(TestCase):
    """Caracteriza el rechazo explícito de aliases retirados en `address`.

    Cada prueba usa un catálogo mínimo realista para que la URL exista en su
    variante canónica y el 404 se deba únicamente a la forma de la ruta, no a
    ausencia de datos de soporte.
    """

    def setUp(self):
        """Construye un catálogo base suficiente para los filtros manuales.

        Se crean país, provincia, ciudad, universidad y campus porque las
        rutas cubiertas combinan detalle por id y filtros activos encadenados.
        """
        self.client = APIClient()

        self.country_ec = Country.objects.create(name="Ecuador", is_active=True)
        self.country_us = Country.objects.create(name="USA", is_active=False)
        self.province_pichincha = Province.objects.create(
            name="Pichincha",
            is_active=True,
            country=self.country_ec,
        )
        self.city_quito = City.objects.create(
            name="Quito",
            is_active=True,
            province=self.province_pichincha,
        )
        self.university_ups = University.objects.create(
            name="UPS",
            is_active=True,
            country=self.country_ec,
        )
        self.university_hidden = University.objects.create(
            name="UTA",
            is_active=False,
            country=self.country_us,
        )
        self.campus_sur = Campus.objects.create(
            name="Campus Sur",
            address="Av. Sur",
            is_active=True,
            university=self.university_ups,
            city=self.city_quito,
        )

    def test_country_detail_rejects_trailing_slash(self):
        """El detalle manual de país ya no acepta slash final."""
        response = self.client.get(f"/api/v1/address/countries/{self.country_ec.id}/")
        self.assertEqual(response.status_code, 404)

    def test_province_by_country_rejects_trailing_slash(self):
        """El filtro manual de provincias por país también quedó sin alias."""
        response = self.client.get(f"/api/v1/address/province/country/{self.country_ec.id}/")
        self.assertEqual(response.status_code, 404)

    def test_countries_active_rejects_trailing_slash(self):
        """El listado manual de países activos expone solo la forma canónica."""
        response = self.client.get("/api/v1/address/countries/active/")
        self.assertEqual(response.status_code, 404)

    def test_universities_by_country_rejects_trailing_slash(self):
        """La consulta de universidades activas por país rechaza la forma legacy."""
        response = self.client.get(f"/api/v1/address/universities/active/{self.country_ec.id}/")
        self.assertEqual(response.status_code, 404)

    def test_campus_by_university_rejects_trailing_slash(self):
        """El filtro de campus por universidad mantiene el mismo criterio de contrato."""
        response = self.client.get(f"/api/v1/address/campus/active/{self.university_ups.id}/")
        self.assertEqual(response.status_code, 404)
