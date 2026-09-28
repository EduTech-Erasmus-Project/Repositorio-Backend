"""Serializers para el catálogo de áreas de conocimiento.

El módulo mezcla serializers completos del modelo con proyecciones reducidas
pensadas para listados, filtros y respuestas adaptadas por idioma.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers, pagination
from rest_framework.validators import UniqueValidator
from .models import (
    KnowledgeArea, 
    )
class KnowledgeAreaSerializer(serializers.ModelSerializer):
    """Serializer completo del modelo para CRUD básico."""

    class Meta:
        model = KnowledgeArea
        fields = ('__all__')
        
class KnowledgeAreaNameSerializer(serializers.ModelSerializer):
    """Salida mínima que proyecta el nombre en español al campo `name`."""

    name = serializers.SerializerMethodField('rename_name')
    class Meta:
        model = KnowledgeArea
        fields = ('name',)

    @extend_schema_field(serializers.CharField())
    def rename_name(self, obj) -> str:
        """Expone `name_es` con el nombre corto esperado por algunos clientes."""
        return obj.name_es

class KnowledgeAreaUpdateSerializer(serializers.Serializer):
    """Valida una actualización simplificada de nombre y descripción."""

    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)

class KnowledgeAreaListSerializers(serializers.ModelSerializer):
    """Serializer de listado que normaliza nombre y descripción al contrato corto."""

    name = serializers.SerializerMethodField('rename_name')
    description = serializers.SerializerMethodField('rename_description')
    class Meta:
        model = KnowledgeArea
        fields = (
            'id',
            'name',
            'description'
        )

    @extend_schema_field(serializers.CharField())
    def rename_name(self, obj) -> str:
        """Proyecta `name_es` al campo `name`."""
        return obj.name_es

    @extend_schema_field(serializers.CharField(allow_null=True))
    def rename_description(self, obj) -> str | None:
        """Proyecta `description_es` al campo `description`."""
        return obj.description_es

class KnowledgeAreaListSerializer(serializers.ModelSerializer):
    """Listado casi completo sin metadatos de auditoria ni campos en inglés."""

    class Meta:
        model = KnowledgeArea
        exclude = ['name_en','description_es','description_en','modified','created']

class KnowledgeAreaEsSerializer(serializers.ModelSerializer):
    """Salida de lectura que usa explícitamente el nombre en español."""

    name = serializers.CharField(source='name_es')
    class Meta(KnowledgeAreaListSerializer.Meta):
        pass
    
class KnowledgeAreaEnSerializer(serializers.ModelSerializer):
    """Salida de lectura que usa explícitamente el nombre en inglés."""

    name = serializers.CharField(source='name_en')
    class Meta(KnowledgeAreaListSerializer.Meta):
        pass
