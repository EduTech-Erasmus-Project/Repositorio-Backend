"""Modelos para registrar interacciones de usuarios con objetos de aprendizaje.

El módulo separa dos tipos de señales:

- interacciones asociadas a un usuario concreto, como likes y descargas
- conteos agregados de visualizaciones del OA
"""

from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.user.models import User
from django.db import models
from model_utils.models import TimeStampedModel

class Interaction(TimeStampedModel):
    """Interacción individual de un usuario con un OA.

    `liked` modela si el usuario marco el OA como favorito y `downloaded`
    conserva un contador heredado de descargas sobre esa misma relación.
    """

    liked = models.BooleanField(
        default=False,
        help_text="Indica si el usuario marco el objeto de aprendizaje como favorito o gustado.",
    )
    downloaded = models.IntegerField(
        default=0,
        help_text="Cantidad de descargas registradas para esta relacion usuario-OA.",
    )
    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        related_name='oa_liked',
        help_text="Objeto de aprendizaje sobre el que el usuario realizo la interaccion.",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_interacted',
        help_text="Usuario que marco like o registro descargas sobre el OA.",
    )

    def __str__(self):
        return str(self.id)


class ViewInteraction(TimeStampedModel):
    """Conteo agregado de visualizaciones registradas para un OA."""

    view = models.IntegerField(
        default=0,
        help_text="Total agregado de visualizaciones registradas para el objeto de aprendizaje.",
    )
    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        related_name='oa_viewed',
        help_text="Objeto de aprendizaje al que pertenece el contador agregado de vistas.",
    )

    def __str__(self):
        return str(self.id)
