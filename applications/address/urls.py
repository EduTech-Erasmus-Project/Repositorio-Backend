from django.urls import path
from . import views

app_name = 'address'
urlpatterns = [

    path('api/v1/address/countries/', views.CountryListCreateAPIView.as_view()),
    path('api/v1/address/countries/<int:pk>', views.CountryRetrieveUpdateDestroyAPIView.as_view()),

    path('api/v1/address/province/', views.ProvinceListCreateAPIView.as_view()),
    path('api/v1/address/province/<int:pk>', views.ProvinceRetrieveUpdateDestroyAPIView.as_view()),
    path('api/v1/address/province/country/<int:pk>', views.ProvinceByCountry.as_view()),

    path('api/v1/address/university/', views.UniversityListCreateAPIView.as_view()),
    path('api/v1/address/university/<int:pk>', views.UniversityRetrieveUpdateDestroyAPIView.as_view()),

    path('api/v1/address/city/', views.CityListCreateAPIView.as_view()),
    path('api/v1/address/city/<int:pk>', views.CityRetrieveUpdateDestroyAPIView.as_view()),

    path('api/v1/address/campus/', views.CampusListCreateAPIView.as_view()),
    path('api/v1/address/campus/<int:pk>', views.CampusRetrieveUpdateDestroyAPIView.as_view()),

    path('api/v1/address/countries/active', views.GetAddressCountriesActiveListAPIView.as_view()),
    path('api/v1/address/cities/active', views.GetAddressCitiesListAPIView.as_view()),
    path('api/v1/address/universities/active', views.GetUniversitiesListAPIView.as_view()),
    path('api/v1/address/campus/active', views.GetCampusListAPIView.as_view()),
    path('api/v1/address/universities-by-city/<int:pk>', views.GetUniversitiesByCityListAPIView.as_view()),
    path('api/v1/address/universities/active/<int:pk>', views.GetUniversitiesByCountryListAPIView.as_view()),
    path('api/v1/address/campus/active/<int:pk>', views.GetCampusByUniversityListAPIView.as_view()),
]
