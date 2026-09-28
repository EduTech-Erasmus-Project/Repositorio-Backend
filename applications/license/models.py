"""Modelos del catálogo de licencias reutilizado por los OAs.

Este modulo define un catálogo pequeño pero estable: el nombre visible en
español, el nombre visible en inglés y un valor corto que suele usarse como
identificador interoperable en formularios, integraciones o filtros.
"""

from django.db import models
from model_utils.models import TimeStampedModel


class License(TimeStampedModel):
    """Catálogo bilingüe de licencias disponibles para un OA.

    `name_es` y `name_en` representan la etiqueta visible según el idioma de
    la interfaz. `value` guarda el identificador corto y único de la licencia,
    que suele ser el dato mas estable para persistencia o compatibilidad entre
    módulos.
    """

    name_es = models.CharField(
        max_length=255,
        unique=True,
        help_text="Nombre visible de la licencia en español.",
    )
    name_en = models.CharField(
        max_length=255,
        unique=True,
        help_text="Nombre visible de la licencia en ingles.",
    )
    value = models.CharField(
        max_length=50,
        unique=True,
        help_text="Identificador corto y unico de la licencia usado por formularios, filtros o integraciones.",
    )

    def __str__(self):
        """Devuelve el nombre en español usado normalmente en administración."""

        return self.name_es
