"""Serializers del catálogo de preferencias y sus filtros auxiliares.

Este módulo mezcla serializers de escritura simple con salidas de lectura mas
ricas para dos usos frecuentes:
- construir el catálogo de preferencias agrupado por área
- exponer mappings auxiliares entre filtros de interfaz y preferencias
"""

from applications.preferences.models import Preferences, PreferencesArea, PreferencesFilter, PreferencesFilterArea
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class PreferencesSerializer(serializers.ModelSerializer):
    """Serializer de escritura o lectura completa del modelo `Preferences`."""

    class Meta:
        model = Preferences
        fields = (
            '__all__'
        )


class PreferencesListSerializer(serializers.ModelSerializer):
    """Salida mínima de una preferencia para listados o selects."""

    class Meta:
        model = Preferences
        fields = (
            'id',
            'description'
        )


class PreferencesListSerializersTest(serializers.ModelSerializer):
    """Listado que agrega un alias obtenido desde `PreferencesFilter`.

    Se usa cuando no basta con mostrar la descripción de la preferencia y hace
    falta exponer también un valor alternativo de búsqueda asociado.
    """

    name = serializers.SerializerMethodField()

    class Meta:
        model = Preferences
        fields = (
            'id',
            'description',
            'name'
        )

    @extend_schema_field(serializers.CharField())
    def get_name(self, obj) -> str:
        """Busca el primer `search_value` relacionado con la preferencia."""

        query = PreferencesFilter.objects.filter(preferences__icontains=obj.description).values('search_value')
        if query.exists():
            return query[0]['search_value']
        return ""


class PreferencesAreaListSerializer(serializers.ModelSerializer):
    """Serializer completo de un área de preferencias."""

    class Meta:
        model = PreferencesArea
        fields = (
            '__all__'
        )


class PreferencesFilterSerializer(serializers.ModelSerializer):
    """Expone el mapping básico entre valor de búsqueda y preferencia textual."""

    class Meta:
        model = PreferencesFilter
        fields = (
            'search_value',
            'preferences'
        )


class PreferencesAreaFilterSerializer(serializers.ModelSerializer):
    """Agrupa filtros auxiliares por área con sus mappings anidados."""

    preferences_filter = PreferencesFilterSerializer(many=True)

    class Meta:
        model = PreferencesFilterArea
        fields = (
            'filters_area',
            'preferences_filter'
        )


class PreferencesByAreaSerializer(serializers.ModelSerializer):
    """Devuelve una área con la lista de preferencias que contiene.

    Esta salida es útil para el frontend cuando necesita renderizar el catálogo
    ya agrupado, sin tener que reconstruir las relaciones en cliente.
    """

    preferences = PreferencesListSerializer(many=True)

    class Meta:
        model = PreferencesArea
        fields = (
            'id',
            'preferences_are',
            'preferences'
        )
