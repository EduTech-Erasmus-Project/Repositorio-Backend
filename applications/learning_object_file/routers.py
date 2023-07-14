from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/learning-object-file', views.LearningObjectModelViewSet, basename='learningobject_file')
router.register(r'api/v1/learning-object-file-delete', views.DeleteLearningObjectViewSet, basename='learningobject_delete')
router.register(r'api/v1/learning-object-file-delete-admin', views.DeleteLearningObjectViewSetAdmin, basename='learningobject_delete_admin')
router.register(r'api/v1/learning-object-function-delete', views.funcionDeleteOldFolderAndRegisters, basename= 'deleteFunctions')
urlpatterns = router.urls