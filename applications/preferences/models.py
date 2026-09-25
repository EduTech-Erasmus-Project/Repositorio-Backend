"""Modelos del catálogo de preferencias usado por perfiles y filtros.

Este módulo define dos piezas del dominio:
- el catálogo de preferencias que puede seleccionar un estudiante en su perfil
- una capa auxiliar de filtros que asocia términos o valores de búsqueda con
  categorías de preferencias reutilizadas por otras vistas

"""

from django.db import models
from model_utils.models import TimeStampedModel


class PreferencesArea(TimeStampedModel):
    """Agrupa preferencias del perfil bajo una misma categoría temática.

    Este modelo funciona como cabecera del catálogo visible para el usuario.
    Una instancia puede representar un grupo como accesibilidad, formato o
    cualquier otra familia de preferencias que luego contiene varias opciones.
    """

    preferences_are = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del area que agrupa preferencias seleccionables por el estudiante.",
    )

    def __str__(self):
        """Devuelve el nombre con el que el área se reconoce en administración."""
        return self.preferences_are


class Preferences(TimeStampedModel):
    """Opción individual que un estudiante puede asociar a su perfil.

    `description` es el texto visible de la preferencia. `priority` conserva un
    orden o peso relativo dentro de su área. `preferences_area` conecta cada
    opción con el grupo temático al que pertenece.
    """

    description = models.CharField(
        max_length=100,
        help_text="Texto visible de la preferencia que puede seleccionar el estudiante.",
    )
    priority = models.IntegerField(
        default=1,
        help_text="Orden o prioridad relativa de la preferencia dentro de su area.",
    )
    preferences_area = models.ForeignKey(
        PreferencesArea,
        on_delete=models.CASCADE,
        related_name="preferences",
        help_text="Area tematica a la que pertenece esta preferencia.",
    )

    def __str__(self):
        """Muestra el id y la descripción para listados."""
        return str(self.id) + " " + self.description


class PreferencesFilterArea(TimeStampedModel):
    """Agrupa filtros auxiliares relacionados con una familia de preferencias.

    A diferencia de `PreferencesArea`, este modelo no describe opciones del
    perfil del estudiante sino categorías usadas para organizar mappings de
    filtros o valores de entrada que otras capas del sistema consumen.
    """

    filters_area = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Nombre del grupo de filtros auxiliares relacionado con preferencias.",
    )

    def __str__(self):
        """Devuelve el nombre visible del grupo de filtros."""
        return self.filters_area


class PreferencesFilter(TimeStampedModel):
    """Asocia un valor de búsqueda con una etiqueta o categoría de preferencia.

    Este modelo sirve como tabla de apoyo para traducir términos de interfaz o
    valores de consulta a una clasificación relacionada con preferencias. Por
    eso guarda tanto el `search_value` original como el texto `preferences` que
    representa la categoría o resultado esperado dentro del área de filtros.
    """

    search_value = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Valor o alias que puede llegar desde la interfaz o una consulta de filtro.",
    )
    preferences = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Texto de preferencia asociado al valor de busqueda.",
    )
    preferences_filter_area = models.ForeignKey(
        PreferencesFilterArea,
        on_delete=models.CASCADE,
        related_name="preferences_filter",
        help_text="Grupo de filtros al que pertenece este mapping de preferencia.",
    )

    def __str__(self):
        """Resume el mapping usando el id y el valor de busqueda."""
        return str(self.id) + " " + self.search_value
