"""Router principal del catálogo de profesiones.

Este archivo expone el recurso REST base administrado por `ProfessionView`.
El módulo no necesita rutas manuales adicionales: todo su contrato activo sale
por este router.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/profession', views.ProfessionView, basename='profession')
urlpatterns = router.urls
