from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/license', views.LicenseView, basename='licence')
urlpatterns = router.urls