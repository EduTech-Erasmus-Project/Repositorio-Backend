"""Pruebas de contrato de rutas manuales OER en `learning_object_file`.

La integración OER Adapt expone rutas manuales, no salidas del router. Tras la
limpieza de aliases quedó solo la variante canónica de creación sin slash
final. Esta suite deja documentado ese contrato y evita que el test vuelva a
depender de una ruta retirada.
"""

from django.test import TestCase
from rest_framework.test import APIClient


class LearningObjectFileOerURLCompatibilityTests(TestCase):
    """Caracteriza el contrato actual del endpoint manual de creación OER."""

    def setUp(self):
        """Prepara un cliente anónimo porque la ruta se puede invocar directamente."""
        self.client = APIClient()

    def test_oer_create_uses_canonical_route_without_trailing_slash(self):
        """La ruta canónica responde el 400 esperado cuando falta payload.

        No se prueba aquí el flujo funcional de integración OER, solo que la
        URL que sigue publicada por el backend continúa resolviendo.
        """
        response = self.client.post(
            "/api/v1/learning-object-oer/create",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("id", response.data)
