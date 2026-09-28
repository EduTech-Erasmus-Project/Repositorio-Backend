"""Modelos del catálogo de profesiones usado por el perfil docente.

El módulo es pequeño, pero este catálogo aparece en el alta y actualización de
usuarios con rol `teacher`, por lo que conviene dejar claro que no representa
una profesión laboral del sistema en abstracto sino una opción reutilizable del
perfil académico o profesional del docente.
"""

from django.db import models
from model_utils.models import TimeStampedModel


class Profession(TimeStampedModel):
    """Entrada del catálogo de profesiones asociables a un docente.

    Cada registro representa una etiqueta estable que luego se relaciona con el
    modelo `Teacher`. `description` es única para evitar duplicados visibles en
    formularios, filtros o listados administrativos.
    """

    description = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre visible de la profesion asociable al perfil docente.",
    )

    def __str__(self):
        """Devuelve una representación breve útil en administración y debug."""

        return str(self.id) + ' ' + self.description
