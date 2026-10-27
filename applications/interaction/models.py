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


class ViewRecord(models.Model):
    """Vista ya contada para una referencia, un OA y un día.

    Sirve solo para deduplicar: la misma referencia suma una vista por OA por
    día. Los registros de días anteriores se borran automáticamente.
    """

    reference = models.CharField(
        max_length=64,
        help_text="Valor aleatorio de la referencia firmada que emitió `interaction-ref`.",
    )
    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        related_name='view_records',
        help_text="Objeto de aprendizaje visto.",
    )
    date = models.DateField(
        help_text="Día del servidor en que se contó la vista.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reference', 'learning_object', 'date'],
                name='unique_view_record_per_day',
            ),
        ]


class DownloadRecord(models.Model):
    """Descarga ya contada para una referencia, un OA y un día.

    Misma regla que `ViewRecord`: una descarga por referencia, por OA y por día.
    """

    reference = models.CharField(
        max_length=64,
        help_text="Valor aleatorio de la referencia firmada que emitió `interaction-ref`.",
    )
    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        related_name='download_records',
        help_text="Objeto de aprendizaje descargado.",
    )
    date = models.DateField(
        help_text="Día del servidor en que se contó la descarga.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reference', 'learning_object', 'date'],
                name='unique_download_record_per_day',
            ),
        ]
