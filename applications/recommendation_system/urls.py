"""Rutas manuales del recommendation system.

El módulo expone actualmente una superficie API muy pequeña: la ruta de
recomendaciones personalizadas para el usuario autenticado. El antiguo endpoint
de prueba para generar datasets permanece solo como referencia comentada.
"""

from django.urls import path
from . import views
from rest_framework_simplejwt import views as jwt_views


app_name = 'recommendation_system'
urlpatterns = [
    # Endpoint principal del módulo: devuelve OAs recomendados para el usuario
    # autenticado a partir de interacciones y datasets auxiliares.
    path('api/v1/learning-objects/recommended/', views.LearningObjectRecommended.as_view()),
    # Ruta legacy de diagnóstico, hoy fuera del contrato activo.
    # path('api/v1/dataset-generator/', views.DataSetGeneratorView.as_view(), name='student_list'),
]
