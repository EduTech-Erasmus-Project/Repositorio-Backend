from rest_framework import serializers, pagination
from rest_framework.validators import UniqueValidator
from .models import (
    KnowledgeArea, 
    )
class KnowledgeAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArea
        fields = ('__all__')
        
class KnowledgeAreaNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArea
        fields = ('name',)

class KnowledgeAreaUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)

class KnowledgeAreaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArea
        fields = (
            'id',
            'name',
            'description'
        )