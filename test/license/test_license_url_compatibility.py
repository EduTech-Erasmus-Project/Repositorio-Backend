"""Pruebas de contrato de la ruta manual `endpoint-filter`.

El frontend actual consume la variante sin slash final y ese es el contrato que
este archivo protege.
"""

from django.test import TestCase
from rest_framework.test import APIClient


class LicenseURLCompatibilityTests(TestCase):
    """Verifica que la ruta manual de filtros mantenga su forma canónica."""

    def setUp(self):
        """Usa un cliente anónimo porque el endpoint probado es público."""
        self.client = APIClient()

    def test_endpoint_filter_without_trailing_slash_returns_data(self):
        """La variante canónica sin slash final debe seguir respondiendo."""
        response = self.client.get(
            "/api/v1/endpoint-filter",
            HTTP_ACCEPT_LANGUAGE="es",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["name"], "Licencia")
