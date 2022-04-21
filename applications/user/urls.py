from django.urls import path
from . import views
from rest_framework_simplejwt import views as jwt_views


app_name = 'user_app'
urlpatterns = [
    path('api/v1/login/', views.MyObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/login/', views.MyObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/user/', views.UserAPIView.as_view(), name='user'),
    path('api/v1/user-count/', views.UserCountView.as_view()),
    path('api/v1/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/user/photo/<int:pk>/', views.UpdateUserProfilePicture.as_view(), name='upadte_picture'),
    path('api/v1/user-preferences/email/<str:email>/', views.GetStudentPreferences.as_view(), name='get_preferences'),
    path('api/v1/user/change_password/<int:pk>/', views.ChangePasswordView.as_view(), name='auth_change_password'),
    path('api/v1/orcid-verify/', views.VerifyOrcid.as_view(),name='orcid_verify'),

]