from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/user-preferences', views.UserPrefrencesView, basename='user_preferences')
router.register(r'api/v1/preferences-area', views.PrefrencesAreaView, basename='preferences_area')
# router.register(r'api/v1/user-preferences/email', views.SerachPreferencesApiView, basename='preferences_area')
urlpatterns = router.urls
