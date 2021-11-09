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

class KnowledgeAreaListSerializers(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('rename_name')
    description = serializers.SerializerMethodField('rename_description')
    class Meta:
        model = KnowledgeArea
        fields = (
            'id',
            'name',
            'description'
        )
    def rename_name(self, obj):
        return obj.name_es
    def rename_description(self, obj):
        return obj.description_es

class KnowledgeAreaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArea
        exclude = ['name_es','name_en','description_es','description_en','modified','created']

class KnowledgeAreaEsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_es')
    class Meta(KnowledgeAreaListSerializer.Meta):
        pass
    
class KnowledgeAreaEnSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_en')
    class Meta(KnowledgeAreaListSerializer.Meta):
        pass