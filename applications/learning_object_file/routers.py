"""Routers principales del módulo de archivos de objetos de aprendizaje.

Aqui se registra solo el CRUD principal del archivo OA. Las integraciones
especiales con OER Adapt y los borrados legacy viven en `urls.py` porque
responden a contratos manuales y no a operaciones REST directas.
"""

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()

# CRUD del archivo OA.
router.register(r'api/v1/learning-object-file', views.LearningObjectModelViewSet, basename='learningobject_file')

urlpatterns = router.urls
