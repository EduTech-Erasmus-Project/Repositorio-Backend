"""Modelos para el catálogo de niveles educativos.

El módulo mantiene un catálogo simple y bilingüe que se reutiliza en perfiles
de usuario y filtros del sistema.
"""

from django.db import models
from model_utils.models import TimeStampedModel


class EducationLevel(TimeStampedModel):
    """Nivel educativo disponible en el catálogo del proyecto.

    `name_es` y `name_en` son únicos para evitar duplicados en cada idioma y
    permitir que el mismo catálogo se use en interfaces bilingües.
    """

    name_es = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del nivel educativo en español, usado por defecto en respuestas y formularios.",
    )
    name_en = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del nivel educativo en ingles para interfaces o respuestas bilingues.",
    )

    def __str__(self):
        return str(self.id) + ' ' + self.name_es