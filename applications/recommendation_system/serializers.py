

from applications.user.models import Student, User
from applications.preferences.models import Preferences
from applications.preferences.serializers import PreferencesListSerializer
from applications.learning_object_metadata.models import LearningObjectMetadata
from rest_framework import serializers


class RecommendationSystemSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = Preferences
        fields = (
            'description',
            )
class StudentPreferencesRS(serializers.ModelSerializer):
    preferences  = PreferencesSerializerRS(many=True,read_only=True)
    class Meta:
        model = Student
        fields = ('id','preferences')

# class UserSerializerRS(serializers.ModelSerializer):
#     student = StudentPreferencesRS(read_only=True)
#     class Meta:
#         model = User
#         fields = (
#             'first_name',
#             'last_name',
#             'student'
#         )
