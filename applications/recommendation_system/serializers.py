"""Serializers auxiliares del recommendation system.

Este módulo no define el contrato principal del endpoint recomendado actual,
que reutiliza serializers de `learning_object_metadata`. Aun así, conserva
serializers de apoyo para exponer metadata resumida del OA y preferencias del
estudiante en flujos internos, pruebas o Código legacy del módulo.
"""


from applications.user.models import Student, User
from applications.preferences.models import Preferences
from applications.preferences.serializers import PreferencesListSerializer
from applications.learning_object_metadata.models import LearningObjectMetadata
from rest_framework import serializers


class RecommendationSystemSerializer(serializers.ModelSerializer):
    """Salida resumida de metadata accesible de un objeto de aprendizaje.

    El serializer se enfoca en campos de `LearningObjectMetadata` que pueden ser
    útiles para interfaces o experimentos del recommendation system sin cargar
    toda la metadata pública del OA.
    """

    class Meta:
        model= LearningObjectMetadata
        fields = (
            'id',
            'general_title',
            'accesibility_summary',
            'accesibility_features',
            'accesibility_hazard',
            'accesibility_control',
            'accesibility_api',
        )


class PreferencesSerializerRS(serializers.ModelSerializer):
    """Salida mínima de una preferencia dentro del contexto de recomendación."""

    class Meta:
        model = Preferences
        fields = (
            'description',
            )


class StudentPreferencesRS(serializers.ModelSerializer):    
    """Expone un estudiante junto con sus preferencias anidadas.

    Esta vista resumida resulta útil cuando el recommendation system necesita
    inspeccionar el perfil declarado del estudiante sin cargar todos los campos
    del modelo `Student`.
    """


    preferences  = PreferencesSerializerRS(many=True,read_only=True)

    class Meta:
        model = Student
        fields = ('id','preferences')

# Bloque legacy conservado como referencia histórica; hoy no forma parte del
# contrato activo del modulo.
# class UserSerializerRS(serializers.ModelSerializer):
#     student = StudentPreferencesRS(read_only=True)
#     class Meta:
#         model = User
#         fields = (
#             'first_name',
#             'last_name',
#             'student'
#         )
