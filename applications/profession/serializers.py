from rest_framework import serializers, pagination
from .models import Profession 

class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = (
            '__all__'
        )
class ProfessionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = (
            'id',
            'description'
        )