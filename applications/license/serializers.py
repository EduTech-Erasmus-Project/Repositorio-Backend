
"""Serializers del catálogo de licencias.

Este módulo separa tres contratos sencillos:
- salida corta para clientes que solo necesitan `id`, `name` y `value`
- escritura/CRUD completo para administración
- variantes de lectura que exponen el nombre según el idioma solicitado
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers,pagination
from .models import License


class LicenseSerializer(serializers.ModelSerializer):
    """Salida corta usada por consumidores que solo necesitan el nombre visible."""

    name = serializers.SerializerMethodField('rename_name')

    class Meta:
        model = License
        fields = ('id','name','value')

    @extend_schema_field(serializers.CharField())
    def rename_name(self, obj) -> str:
        """Expone por defecto el nombre en español del catálogo legacy."""

        return obj.name_es


class LicenseRegisterSerializer(serializers.ModelSerializer):
    """Serializer de escritura para crear o actualizar licencias del catálogo."""

    class Meta:
        model = License
        fields = ('id', 'name_es', 'name_en', 'value')


class LicenseListSerializer(serializers.ModelSerializer):
    """Listado administrativo con el valor técnico y campos base del modelo."""

    class Meta:
        model = License
        exclude = ['name_es','name_en','modified','created']


class LicenseEsSerializer(serializers.ModelSerializer):
    """Lectura que pública el nombre en español bajo la clave uniforme `name`."""

    name = serializers.CharField(source='name_es')

    class Meta(LicenseListSerializer.Meta):
        pass


class LicenseEnSerializer(serializers.ModelSerializer):
    """Lectura que pública el nombre en inglés bajo la clave uniforme `name`."""

    name = serializers.CharField(source='name_en')

    class Meta(LicenseListSerializer.Meta):
        pass
