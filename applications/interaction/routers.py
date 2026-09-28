"""Recursos expuestos por router en el módulo de interacciones.

El router solo pública el CRUD principal de `InteractionAPIView`, es decir, la
relación usuario-OA usada para likes y descargas. Los contadores agregados,
rankings públicos y el flujo `interaction-ref` viven en `urls.py` porque usan
vistas manuales y contratos distintos al CRUD base.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Recurso principal de interacción usuario-OA.
router.register(r'api/v1/object-learning/interaction', views.InteractionAPIView, basename='user-interaction')
urlpatterns = router.urls
