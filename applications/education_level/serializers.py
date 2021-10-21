from rest_framework import serializers, pagination
from applications.education_level.models import EducationLevel
class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = (
            '__all__'
        )
class EducationLevelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = (
            'id',
            'name'
        )