from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# router.register(r'api/v1/learning-objects-to-approved', views.AdminLearningObjectAproved, basename='learningobject_admin_aproved')
# router.register(r'api/v1/learning-objects-update-public', views.UpdatePublicLearningObject, basename='learningobject_admin_disaproved')
router.register(r'api/v1/learning-object-metadata', views.LearningObjectMetadataViewSet, basename='learning_object_metadata')
router.register(r'api/v1/learning-object/create/commentary', views.CommentaryModelView, basename='create-commentary')
urlpatterns = router.urls