from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/profession', views.ProfessionView, basename='profession')
urlpatterns = router.urls