"""Rutas del módulo de catálogos de dirección.

El archivo mezcla dos familias de endpoints:

- CRUD básico de países, provincias, ciudades, universidades y campus
- consultas públicas de catálogos activos y filtros auxiliares

Varias rutas existen con y sin slash final para conservar compatibilidad con
clientes legacy del frontend.
"""

from django.urls import path
from . import views

app_name = 'address'

# Alias locales para mantener legible la declaración de rutas.
country_list_view = views.CountryListCreateAPIView.as_view()
country_detail_view = views.CountryRetrieveUpdateDestroyAPIView.as_view()
province_list_view = views.ProvinceListCreateAPIView.as_view()
province_detail_view = views.ProvinceRetrieveUpdateDestroyAPIView.as_view()
province_by_country_view = views.ProvinceByCountry.as_view()
university_list_view = views.UniversityListCreateAPIView.as_view()
university_detail_view = views.UniversityRetrieveUpdateDestroyAPIView.as_view()
city_list_view = views.CityListCreateAPIView.as_view()
city_detail_view = views.CityRetrieveUpdateDestroyAPIView.as_view()
campus_list_view = views.CampusListCreateAPIView.as_view()
campus_detail_view = views.CampusRetrieveUpdateDestroyAPIView.as_view()
countries_active_view = views.GetAddressCountriesActiveListAPIView.as_view()
cities_active_view = views.GetAddressCitiesListAPIView.as_view()
universities_active_view = views.GetUniversitiesListAPIView.as_view()
campus_active_view = views.GetCampusListAPIView.as_view()
universities_by_city_view = views.GetUniversitiesByCityListAPIView.as_view()
universities_by_country_view = views.GetUniversitiesByCountryListAPIView.as_view()
campus_by_university_view = views.GetCampusByUniversityListAPIView.as_view()

urlpatterns = [
    # CRUD de países.
    path('api/v1/address/countries/', country_list_view),
    path('api/v1/address/countries/<int:pk>', country_detail_view),

    # CRUD y filtros de provincias.
    path('api/v1/address/province/', province_list_view),
    path('api/v1/address/province/<int:pk>', province_detail_view),
    path('api/v1/address/province/country/<int:pk>', province_by_country_view),

    # CRUD de universidades.
    path('api/v1/address/university/', university_list_view),
    path('api/v1/address/university/<int:pk>', university_detail_view),

    # CRUD de ciudades.
    path('api/v1/address/city/', city_list_view),
    path('api/v1/address/city/<int:pk>', city_detail_view),

    # CRUD de campus.
    path('api/v1/address/campus/', campus_list_view),
    path('api/v1/address/campus/<int:pk>', campus_detail_view),

    # Catálogos activos y filtros públicos auxiliares.
    path('api/v1/address/countries/active', countries_active_view),
    path('api/v1/address/cities/active', cities_active_view),
    path('api/v1/address/universities/active', universities_active_view),
    path('api/v1/address/campus/active', campus_active_view),
    path('api/v1/address/universities-by-city/<int:pk>', universities_by_city_view),
    path('api/v1/address/universities/active/<int:pk>', universities_by_country_view),
    path('api/v1/address/campus/active/<int:pk>', campus_by_university_view),
]
