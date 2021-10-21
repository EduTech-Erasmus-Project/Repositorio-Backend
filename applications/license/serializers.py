
from rest_framework import serializers,pagination
from .models import License
class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ('id','name','value')