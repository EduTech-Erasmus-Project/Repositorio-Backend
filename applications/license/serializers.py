
from rest_framework import serializers,pagination
from .models import License
class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ('id','name_es','value')

class LicenseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        exclude = ['name_es','name_en','modified','created']

class LicenseEsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_es')
    class Meta(LicenseListSerializer.Meta):
        pass
    
class LicenseEnSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_en')
    class Meta(LicenseListSerializer.Meta):
        pass