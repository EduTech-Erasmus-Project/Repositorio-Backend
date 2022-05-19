from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/learning-object-file', views.LearningObjectModelViewSet, basename='learningobject_file')
router.register(r'api/v1/learning-object-file-delete', views.DeleteLearningObjectViewSet, basename='learningobject_delete')
urlpatterns = router.urls