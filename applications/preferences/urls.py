"""Rutas manuales del módulo de preferencias.

El CRUD principal del catálogo sale por router. Este archivo conserva rutas
manuales para endpoints auxiliares, en especial el listado de áreas de filtros
que el frontend usa al construir formularios o filtros de objetos de
aprendizaje.
"""

from rest_framework.routers import DefaultRouter

from django.contrib import admin
from django.urls import path
from . import views


app_name = 'preferences'
urlpatterns = [
    # El frontend actual consume la variante sin slash final.
    path('api/v1/learning-object/filters/area', views.AreaFilters.as_view(), name="filtesr_area"),
    # Estas rutas quedaron como referencia histórica, pero hoy no forman parte
    # del contrato activo expuesto por el módulo.
    # path('api/v1/user-preferences/email/', views.PreferencesByEmail.as_view(), name='preferences_email')
    # path('api/v1/user-preferences/email/', views.SerachPreferencesApiView.as_view()),
    
]
