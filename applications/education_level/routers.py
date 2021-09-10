from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'api/v1/education-level', views.EducationLevelView, basename='education_level')
urlpatterns = router.urls