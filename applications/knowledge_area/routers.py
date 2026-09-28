"""Recursos expuestos por router en el catálogo de áreas de conocimiento.

El router pública un único `ViewSet` para el catálogo bilingüe de áreas de
conocimiento. La parte más particular del contrato vive en `views.py`, donde
el listado se adapta según `Accept-Language`.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Recurso principal del catálogo de áreas de conocimiento.
router.register(r'api/v1/knowledge-area', views.KnowledgeAreaView, basename='areas_de_conocimiento')
urlpatterns = router.urls
