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
    isced_code = models.PositiveSmallIntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="Nivel CINE 2011 de la UNESCO (0 a 8). Define el orden del catálogo.",
    )
    typical_age_min = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Edad típica de inicio del nivel; el formulario del OA la propone como edad mínima.",
    )
    typical_age_max = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Edad típica de fin del nivel; vacío significa sin límite superior.",
    )

    class Meta:
        # Orden CINE; los niveles sin código quedan al final.
        ordering = [models.F('isced_code').asc(nulls_last=True), 'id']

    def __str__(self):
        return str(self.id) + ' ' + self.name_es