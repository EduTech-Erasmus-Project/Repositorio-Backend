"""Pruebas de contrato de rutas manuales del módulo `preferences`.

Este archivo cubre un caso puntual pero importante para frontend: el endpoint
manual que lista áreas de filtros de preferencias. Después de la limpieza de
aliases ya no se preservó la variante con slash final, por lo que el contrato
vigente debe quedar documentado por prueba.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from applications.preferences.models import PreferencesFilterArea


class PreferencesURLCompatibilityTests(TestCase):
    """Valida la forma canónica del endpoint manual de áreas de filtro."""

    def setUp(self):
        """Crea el mínimo catálogo necesario para que el endpoint devuelva datos.

        La prueba usa un solo registro porque aquí no interesa el contenido del
        catálogo, sino confirmar que la ruta canónica sigue resolviendo y
        devolviendo datos tras la limpieza del contrato.
        """
        self.client = APIClient()
        PreferencesFilterArea.objects.create(filters_area="Compatibilidad URL")

    def test_area_filters_uses_canonical_route_without_trailing_slash(self):
        """La ruta sin slash final debe mantenerse como única forma soportada."""
        response = self.client.get("/api/v1/learning-object/filters/area")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["filters_area"], "Compatibilidad URL")
