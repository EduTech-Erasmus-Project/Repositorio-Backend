from rest_framework import serializers
from applications.education_level.models import EducationLevel
class EducationLevelSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('rename_name')
    class Meta:
        model = EducationLevel
        fields = ['id','name']
    def rename_name(self, obj):
        return obj.name_es
        
class EducationLevelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        exclude = ['name_es','name_en','modified','created']

class EducationLevelEsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_es')
    class Meta(EducationLevelListSerializer.Meta):
        pass
    
class EducationLevelEnSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_en')
    class Meta(EducationLevelListSerializer.Meta):
        pass
        