from rest_framework import serializers,pagination
from .models import LearningObjectFile

class LearningObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningObjectFile
        fields = ('__all__')

class LearningObjectOerAdapt(serializers.Serializer):
    key = serializers.CharField(max_length=200)
    urlZip = serializers.URLField(max_length=300)
   # urlPrev = serializers.URLField(max_length=300)
    IdOa = serializers.IntegerField()
    IdOer = serializers.IntegerField()

class LearningObjectFileOerDataSerializer(serializers.Serializer):
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
    id = serializers.IntegerField()
    user_key = serializers.CharField(max_length=200)
    data = LearningObjectFileOerDataSerializer()


class LearningObjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningObjectFile
        fields = ('__all__')
