"""Modelos base para archivos de objetos de aprendizaje.

Este módulo representa el paquete OA cargado al repositorio antes o junto con
su metadata derivada. También conserva campos usados por la integración con
OER Adapt y sus previews asociadas.
"""

from model_utils.models import TimeStampedModel
from django.db import models

from roabackend.storage_backends import PublicMediaStorage


class LearningObjectFile(TimeStampedModel):
    """Archivo comprimido del OA y datos operativos asociados a su carga.

    El registro guarda tanto información local del ZIP cargado por el docente
    como referencias auxiliares para el flujo de integración con OER Adapt.
    """

    file = models.FileField(
        upload_to='oazip',
        blank=False,
        help_text="Archivo ZIP del objeto de aprendizaje cargado al repositorio.",
    )
    url = models.URLField(
        editable=False,
        max_length=300,
        help_text="URL interna generada para acceder al paquete OA almacenado.",
    )
    file_name = models.CharField(
        editable=False,
        max_length=100,
        help_text="Nombre del archivo cargado, conservado para trazabilidad y respuestas de API.",
    )
    file_size = models.IntegerField(
        editable=False,
        blank=True,
        null=True,
        help_text="Tamano del archivo en bytes, usado para informar o validar la carga.",
    )
    path_origin = models.TextField(
        blank=True,
        null=True,
        help_text="Ruta original del paquete procesado en el servidor o durante la extraccion.",
    )
    # Estos campos se completan cuando el OA se sincroniza con OER Adapt.
    oa_integration_id = models.IntegerField(
        blank=True,
        null=True,
        help_text="Identificador externo del OA en el servicio OER Adapt.",
    )
    oa_created_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de creacion reportada por OER Adapt para el OA integrado.",
    )
    oa_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de expiracion reportada por OER Adapt para enlaces o previews temporales.",
    )
    oa_preview_origin = models.URLField(
        max_length=300,
        blank=True,
        null=True,
        help_text="URL de preview del OA original antes de una adaptacion.",
    )
    oa_preview_adapted = models.URLField(
        max_length=300,
        blank=True,
        null=True,
        help_text="URL de preview del OA adaptado generado por OER Adapt.",
    )
    oa_oer_adap_url= models.URLField(
        max_length=300,
        blank=True,
        null=True,
        help_text="URL del recurso o flujo asociado en OER Adapt.",
    )

    REQUIRED_FIELDS = ['file','file_name','file_size']
    
    def __str__(self):
        """Devuelve el identificador del archivo OA para usos internos."""

        return str(self.id)
