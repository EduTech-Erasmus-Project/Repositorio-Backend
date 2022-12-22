from django.urls import path
from . import views

from rest_framework_simplejwt import views as jwt_views

app_name = 'learning_object_file'

urlpatterns = [
    path('api/v1/learning-object-oer/', views.getDataNewLearningObject.as_view(), name='learningobject-oeradap'),
    path('api/v1/learning-object-oer/create', views.saveDataIntegrationWithOer.as_view(), name='learningobject-oeradap-create')
]