from rest_framework import serializers
from applications.address.models import City, University, Campus, Province, Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class ProvinceSerializerWithCountry(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = Province
        fields = "__all__"


class ProvinceSerializer(serializers.ModelSerializer):
    # country = CountrySerializer()
    class Meta:
        model = Province
        fields = "__all__"


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = "__all__"


class CitiesSerializer(serializers.ModelSerializer):
    province = ProvinceSerializer()

    class Meta:
        model = City
        fields = "__all__"


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = "__all__"


class UniversitySerializerWithCountry(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = University
        fields = "__all__"


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = "__all__"


class FullCampusSerializer(serializers.ModelSerializer):
    university = UniversitySerializer()
    city = CitySerializer()
    class Meta:
        model = Campus
        fields = "__all__"