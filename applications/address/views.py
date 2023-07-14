from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework import generics, status
from applications.address.models import City, University, Campus, Country, Province
from applications.address.serializers import CitiesSerializer, UniversitySerializer, CampusSerializer, \
    CountrySerializer, ProvinceSerializer, CitySerializer, ProvinceSerializerWithCountry, \
    UniversitySerializerWithCountry, FullCampusSerializer
from rest_framework.response import Response


class GetAddressCountriesActiveListAPIView(generics.ListAPIView):
    queryset = Country.objects.filter(is_active=True).order_by('id')
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


# Create your views here.
class GetAddressCitiesListAPIView(generics.ListAPIView):
    queryset = City.objects.filter(is_active=True).order_by('id')
    serializer_class = CitiesSerializer
    permission_classes = [AllowAny]


class GetUniversitiesByCountryListAPIView(generics.ListAPIView):
    queryset = University.objects.filter(is_active=True).order_by('id')
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        query = self.queryset.filter(country_id=pk).order_by('id')
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetUniversitiesByCityListAPIView(generics.ListAPIView):
    queryset = University.objects.filter(is_active=True)
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        country = get_object_or_404(Country, province__city__id=pk)
        query = self.queryset.filter(country_id=country.id).order_by('id')
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetUniversitiesListAPIView(generics.ListAPIView):
    queryset = University.objects.filter(is_active=True)
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]


class GetCampusListAPIView(generics.ListAPIView):
    queryset = Campus.objects.filter(is_active=True)
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]


class GetCampusByUniversityListAPIView(generics.ListAPIView):
    queryset = Campus.objects.filter(is_active=True).order_by('id')
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        query = self.queryset.filter(university_id=pk).order_by('id')
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CountryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Country.objects.all().order_by('id')
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


class CountryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


class ProvinceListCreateAPIView(generics.ListCreateAPIView):
    queryset = Province.objects.all().order_by('id')
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        serializer = ProvinceSerializerWithCountry(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProvinceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


class ProvinceByCountry(generics.ListCreateAPIView):
    queryset = Province.objects.all().order_by('id')
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request, pk):
        query = self.queryset.filter(country_id=pk).order_by('id')
        serializer = ProvinceSerializerWithCountry(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CityListCreateAPIView(generics.ListCreateAPIView):
    queryset = City.objects.all().order_by('id')
    serializer_class = CitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        serializer = CitiesSerializer(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CityRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


class UniversityListCreateAPIView(generics.ListCreateAPIView):
    queryset = University.objects.all().order_by('id')
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        serializer = UniversitySerializerWithCountry(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UniversityRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


class CampusListCreateAPIView(generics.ListCreateAPIView):
    queryset = Campus.objects.all().order_by('id')
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        serializer = FullCampusSerializer(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CampusRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin
