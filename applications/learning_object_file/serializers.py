"""Serializers para carga local de OAs e integración con OER Adapt."""

from rest_framework import serializers,pagination
from .models import LearningObjectFile

class LearningObjectSerializer(serializers.ModelSerializer):
    """Serializer base del archivo OA almacenado en el repositorio.

    Se usa tanto para crear el ZIP inicial como para exponer los datos
    persistidos del archivo cargado.
    """

    class Meta:
        model = LearningObjectFile
        fields = ('__all__')

class LearningObjectOerAdapt(serializers.Serializer):
    """Payload mínimo enviado desde OER Adapt para crear o refrescar un OA."""

    key = serializers.CharField(max_length=200)
    urlZip = serializers.URLField(max_length=300)
   # urlPrev = serializers.URLField(max_length=300)
    IdOa = serializers.IntegerField()
    IdOer = serializers.IntegerField()

class LearningObjectFileOerDataSerializer(serializers.Serializer):
    """Bloque `data` de la integración con metadatos operativos de OER."""

    id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    user_ref = serializers.CharField(max_length=200)
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    preview_origin = serializers.URLField(max_length=300)
    preview_adapted = serializers.URLField(max_length=300)
    roa = serializers.BooleanField()
    oer_adap = serializers.URLField(max_length=300)

class LearningObjectFileOerSerializer(serializers.Serializer):
    """Payload completo devuelto por OER para guardar datos de integración."""

    id = serializers.IntegerField()
    user_key = serializers.CharField(max_length=200)
    data = LearningObjectFileOerDataSerializer()


class LearningObjectFileSerializer(serializers.ModelSerializer):
    """Lectura directa del modelo `LearningObjectFile` sin transformaciones."""

    class Meta:
        model = LearningObjectFile
        fields = ('__all__')
