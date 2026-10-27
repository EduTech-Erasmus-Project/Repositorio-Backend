"""Serializers para interacciones de usuarios con objetos de aprendizaje.

El módulo separa serializers para:

- representar la relación completa `Interaction`
- validar cambios puntuales de likes y descargas
- validar el contador agregado de vistas
- transportar agregados simples, como el ranking de mas gustados
"""

from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.interaction.models import Interaction, ViewInteraction
from rest_framework import serializers


class InteractionAllService(serializers.ModelSerializer):
    """Expone la relación completa de interacción usuario-OA."""

    class Meta:
        model = Interaction
        fields = ('id','liked','downloaded','user','learning_object')
    

class InteractionSerializer(serializers.Serializer):
    """Valida la carga base para crear o actualizar una interacción."""

    liked = serializers.BooleanField(
        default=False,
        help_text='Indica si el usuario marca el objeto de aprendizaje como favorito o gustado.',
    )
    downloaded = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text='Contador de descargas asociado a la relación usuario-OA.',
    )
    learning_object = serializers.PrimaryKeyRelatedField(
        queryset=LearningObjectMetadata.objects.all(),
        help_text='Identificador del objeto de aprendizaje sobre el que se registra la interacción.',
    )


class InteractionLikeUpdateSerializer(serializers.Serializer):
    """Valida el cambio puntual del estado liked."""

    liked = serializers.BooleanField(
        help_text='Nuevo estado del like para la interacción existente.',
    )


REFERENCE_HELP_TEXT = (
    'Referencia firmada emitida por `interaction-ref`. Con referencia válida se suma una vez '
    'por OA y por día; sin referencia no se suma.'
)


class InteractionDownloadUpdateSerializer(serializers.Serializer):
    """Valida el registro de una descarga sobre el OA de la URL."""

    downloaded = serializers.IntegerField(
        min_value=0,
        required=False,
        help_text='Obsoleto: se acepta por compatibilidad pero se ignora; el backend suma 1.',
    )
    reference = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text=REFERENCE_HELP_TEXT,
    )


class InteractionDownloadCreateSerializer(InteractionDownloadUpdateSerializer):
    """Valida el registro de una descarga indicando el OA en el cuerpo."""

    learning_object = serializers.PrimaryKeyRelatedField(
        queryset=LearningObjectMetadata.objects.all(),
        help_text='Identificador del objeto de aprendizaje descargado.',
    )


class InteractionMostLiked(serializers.Serializer):
    """Transporta el agregado usado por el ranking de OAs con más likes."""

    learning_object_id = serializers.CharField(
        help_text='Identificador del objeto de aprendizaje agregado.',
    )
    total = serializers.IntegerField(
        help_text='Cantidad total de interacciones con liked=True para ese objeto.',
    )


class InteractionViewUpdateSerializer(serializers.Serializer):
    """Valida el registro de una vista sobre el OA de la URL."""

    view = serializers.IntegerField(
        min_value=0,
        required=False,
        help_text='Obsoleto: se acepta por compatibilidad pero se ignora; el backend suma 1.',
    )
    learning_object = serializers.PrimaryKeyRelatedField(
        queryset=LearningObjectMetadata.objects.all(),
        required=False,
        help_text='Obsoleto: se acepta por compatibilidad; manda el OA de la URL.',
    )
    reference = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text=REFERENCE_HELP_TEXT,
    )


class InteractionViewCreateSerializer(InteractionViewUpdateSerializer):
    """Valida el registro de una vista indicando el OA en el cuerpo."""

    learning_object = serializers.PrimaryKeyRelatedField(
        queryset=LearningObjectMetadata.objects.all(),
        help_text='Identificador del objeto de aprendizaje visto.',
    )


class InteractionViewSerializer(serializers.ModelSerializer):
    """Expone el contador agregado de vistas de un OA."""

    class Meta:
        model = ViewInteraction
        fields = ('view',)


class UserRefSerializer(serializers.Serializer):
    """Valida la clave compartida usada por el endpoint `interaction-ref`."""

    key_ref = serializers.CharField(
        max_length=10,
        help_text='Clave compartida que debe coincidir con la variable de entorno KEY_REF.',
    )
