"""Serializers para el catálogo de niveles educativos.

El módulo expone varias vistas del mismo modelo:

- una salida reducida con `id` y `name`
- una salida de listado casi completa
- un serializer de escritura para alta/edición
- variantes de lectura que proyectan el nombre en español o inglés
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from applications.education_level.models import EducationLevel


class EducationLevelSerializer(serializers.ModelSerializer):
    """Salida reducida que normaliza el nombre al campo `name` en español."""

    name = serializers.SerializerMethodField('rename_name')
    class Meta:
        model = EducationLevel
        fields = ['id','name']

    @extend_schema_field(serializers.CharField())
    def rename_name(self, obj) -> str:
        """Proyecta `name_es` al contrato corto esperado por el frontend."""
        return obj.name_es
        
class EducationLevelListSerializer(serializers.ModelSerializer):
    """Serializer de listado casi completo, sin metadatos de auditoría."""

    class Meta:
        model = EducationLevel
        exclude = ['name_en','modified','created']


class EducationLevelRegisterSerializer(serializers.ModelSerializer):
    """Serializer de escritura para registrar o editar niveles bilingües."""

    class Meta:
        model = EducationLevel
        fields = ['id', 'name_es', 'name_en']


class EducationLevelEsSerializer(serializers.ModelSerializer):
    """Salida de lectura que proyecta explícitamente el nombre en español."""

    name = serializers.CharField(source='name_es')
    class Meta(EducationLevelListSerializer.Meta):
        pass

class EducationLevelEnSerializer(serializers.ModelSerializer):
    """Salida de lectura que proyecta explícitamente el nombre en inglés."""

    name = serializers.CharField(source='name_en')
    class Meta(EducationLevelListSerializer.Meta):
        pass
