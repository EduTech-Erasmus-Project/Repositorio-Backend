"""Modelos para el catálogo de áreas de conocimiento.

El módulo mantiene un catálogo bilingüe reutilizado en perfiles de usuario,
metadatos de OA y filtros del sistema.
"""

from django.db import models
from model_utils.models import TimeStampedModel

class KnowledgeArea(TimeStampedModel):
    """Area de conocimiento disponible en el catálogo del proyecto.

    Los nombres en español e inglés son únicos y las descripciones son
    opcionales para permitir un catálogo breve o más explicativo según el uso.
    """

    name_es = models.CharField(
        max_length=250,
        unique=True,
        help_text="Nombre del area de conocimiento en español, usado por defecto en filtros y respuestas.",
    )
    description_es = models.TextField(
        blank=True,
        null=True,
        help_text="Descripcion opcional del area de conocimiento en español.",
    )
    name_en = models.CharField(
        max_length=250,
        unique=True,
        help_text="Nombre del area de conocimiento en ingles para interfaces o respuestas bilingues.",
    )
    description_en = models.TextField(
        blank=True,
        null=True,
        help_text="Descripcion opcional del area de conocimiento en ingles.",
    )

    def __str__(self):
        return self.name_es
