from rest_framework.routers import DefaultRouter

from django.contrib import admin
from django.urls import path
from . import views


app_name = 'preferences'
urlpatterns = [
    path('api/v1/learning-object/filters/area', views.AreaFilters.as_view(), name="filtesr_area"),
    # path('api/v1/user-preferences/email/', views.PreferencesByEmail.as_view(), name='preferences_email')
    # path('api/v1/user-preferences/email/', views.SerachPreferencesApiView.as_view()),
    
]