"""Serializers del catálogo de profesiones.

Este módulo mantiene dos contratos sencillos:
- un serializer completo para altas, ediciones o lectura total del modelo
- una salida mínima para listados o selects donde solo importan `id` y
  `description`
"""

from rest_framework import serializers, pagination
from .models import Profession 


class ProfessionSerializer(serializers.ModelSerializer):
    """Serializer completo del modelo `Profession`.

    Se usa en las operaciones de escritura del catálogo y en lecturas donde el
    cliente necesita la representación completa del recurso.
    """

    class Meta:
        model = Profession
        fields = (
            '__all__'
        )


class ProfessionListSerializer(serializers.ModelSerializer):
    """Salida mínima del catálogo para listados o campos de selección."""

    class Meta:
        model = Profession
        fields = (
            'id',
            'description'
        )
