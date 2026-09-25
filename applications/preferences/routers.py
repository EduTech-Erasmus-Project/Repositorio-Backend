"""Router principal del módulo de preferencias.

Aqui viven los dos recursos REST base del módulo:
- preferencias individuales del catálogo
- áreas que agrupan esas preferencias

Los endpoints auxiliares que no encajan bien como CRUD puro, como el listado
manual de filtros para objetos de aprendizaje, permanecen en `urls.py`.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/user-preferences', views.UserPrefrencesView, basename='user_preferences')
router.register(r'api/v1/preferences-area', views.PrefrencesAreaView, basename='preferences_area')
# Ruta histórica mantenida solo como referencia; hoy no forma parte del
# contrato activo del router.
# router.register(r'api/v1/user-preferences/email', views.SerachPreferencesApiView, basename='preferences_area')
urlpatterns = router.urls
