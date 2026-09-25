"""Rutas manuales del módulo de licencias.

El CRUD principal del catálogo sale por router. Este archivo solo conserva el
endpoint auxiliar `endpoint-filter`, que el frontend usa para descubrir las
URLs base de algunos catálogos relacionados con filtros.
"""

from django.urls import path
from . import views

app_name = 'licenses'

endpoint_filter_view = views.EndpontFilter.as_view()

urlpatterns = [
    # El frontend actual consume la variante sin slash final.
    path('api/v1/endpoint-filter', endpoint_filter_view),
]
