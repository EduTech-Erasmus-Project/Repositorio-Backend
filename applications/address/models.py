"""Modelos de catálogo geográfico e institucional.

Este módulo define la jerarquía básica usada en perfiles de usuario y filtros:

- país
- provincia
- ciudad
- universidad
- campus

Todos se manejan como catálogos activables/desactivables con `is_active`,
sin borrado lógico adicional.
"""

from django.db import models
from model_utils.models import TimeStampedModel


class Country(TimeStampedModel):
    """País disponible en los catálogos del sistema."""

    name = models.CharField(
        max_length=100,
        help_text="Nombre del pais disponible para registro, filtros y reportes.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el pais esta disponible para ser seleccionado en la plataforma.",
    )

    def __str__(self):
        return str(self.name)


class Province(TimeStampedModel):
    """Provincia o estado asociado a un país."""

    name = models.CharField(
        max_length=100,
        help_text="Nombre de la provincia o estado dentro del catalogo geografico.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la provincia esta disponible para seleccion y filtros.",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="province",
        help_text="Pais al que pertenece la provincia.",
    )

    def __str__(self):
        return str(self.name)


class City(TimeStampedModel):
    """Ciudad asociada a una provincia del catálogo."""

    name = models.CharField(
        max_length=100,
        help_text="Nombre de la ciudad dentro del catalogo geografico.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la ciudad esta disponible para seleccion y filtros.",
    )
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        related_name="city",
        help_text="Provincia a la que pertenece la ciudad.",
    )

    def __str__(self):
        return str(self.name)


class University(TimeStampedModel):
    """Universidad disponible para perfiles y formularios del proyecto.

    `country` permite `null` por compatibilidad con datos legacy que existían
    antes de exigir la relación geográfica completa.
    """

    name = models.CharField(
        max_length=200,
        help_text="Nombre de la universidad disponible para perfiles academicos.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la universidad esta disponible para registro, filtros y reportes.",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="university",
        null=True,
        help_text="Pais asociado a la universidad.",
    )

    def __str__(self):
        return str(self.name)


class Campus(TimeStampedModel):
    """Sede o campus perteneciente a una universidad.

    `city` permite `null` para conservar compatibilidad con registros antiguos
    donde solo se cargaba la universidad y la dirección textual.
    """

    name = models.CharField(
        max_length=100,
        help_text="Nombre del campus universitario.",
    )
    address = models.CharField(
        max_length=300,
        help_text="Direccion textual del campus o sede.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el campus esta disponible para registro, filtros y reportes.",
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="campus",
        help_text="Universidad a la que pertenece el campus.",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="campus_city",
        null=True,
        help_text="Ciudad asociada al campus; permite null por compatibilidad con datos legacy.",
    )

    def __str__(self):
        return str(self.name)
