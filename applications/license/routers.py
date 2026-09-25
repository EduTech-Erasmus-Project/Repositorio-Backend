"""Router principal del catálogo de licencias.

Este archivo publica el CRUD REST base de `LicenseView`. Los endpoints
auxiliares que no encajan como recurso del router, como `endpoint-filter`,
siguen definidos en `urls.py`.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/license', views.LicenseView, basename='licence')
urlpatterns = router.urls
