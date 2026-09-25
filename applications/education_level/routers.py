"""Recursos expuestos por router en el catálogo de niveles educativos.

El router pública un único `ModelViewSet` sobre `EducationLevelView`. La parte
interesante del contrato no está aquí sino en la vista: lectura pública y
listado adaptado por idioma mediante `Accept-Language`.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Recurso principal del catálogo bilingue de niveles educativos.
router.register(r'api/v1/education-level', views.EducationLevelView, basename='education_level')
urlpatterns = router.urls
