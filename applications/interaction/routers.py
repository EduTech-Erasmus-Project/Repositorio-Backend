from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/object-learning/interaction', views.InteractionAPIView, basename='user-interaction')
urlpatterns = router.urls