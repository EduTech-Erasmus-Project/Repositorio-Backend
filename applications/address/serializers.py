"""Serializers para catálogos de dirección e institución.

El módulo distingue serializers planos, útiles para escritura o CRUD básico,
de serializers con relaciones anidadas pensados para respuestas más completas
en vistas de lectura.
"""

from rest_framework import serializers
from applications.address.models import City, University, Campus, Province, Country


class CountrySerializer(serializers.ModelSerializer):
    """Serializer plano para paises del catálogo."""

    class Meta:
        model = Country
        fields = "__all__"


class ProvinceSerializerWithCountry(serializers.ModelSerializer):
    """Serializer de lectura que anida el país asociado a la provincia."""

    country = CountrySerializer()

    class Meta:
        model = Province
        fields = "__all__"


class ProvinceSerializer(serializers.ModelSerializer):
    """Serializer plano para provincias, sin anidar el país."""

    class Meta:
        model = Province
        fields = "__all__"


class CitySerializer(serializers.ModelSerializer):
    """Serializer plano para ciudades."""

    class Meta:
        model = City
        fields = "__all__"


class CitiesSerializer(serializers.ModelSerializer):
    """Serializer de lectura que incluye la provincia anidada de la ciudad."""

    province = ProvinceSerializer()

    class Meta:
        model = City
        fields = "__all__"


class UniversitySerializer(serializers.ModelSerializer):
    """Serializer plano para universidades."""

    class Meta:
        model = University
        fields = "__all__"


class UniversitySerializerWithCountry(serializers.ModelSerializer):
    """Serializer de lectura que anida el país asociado a la universidad."""

    country = CountrySerializer()

    class Meta:
        model = University
        fields = "__all__"


class CampusSerializer(serializers.ModelSerializer):
    """Serializer plano para campus o sedes."""

    class Meta:
        model = Campus
        fields = "__all__"


class FullCampusSerializer(serializers.ModelSerializer):
    """Serializer de lectura completa para campus con universidad y ciudad anidadas."""

    university = UniversitySerializer()
    city = CitySerializer()
    class Meta:
        model = Campus
        fields = "__all__"
