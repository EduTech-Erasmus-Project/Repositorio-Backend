from rest_framework import serializers,pagination
from .models import LearningObjectFile

class LearningObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningObjectFile
        fields = ('__all__')
