from django.urls import path
from . import views

app_name = 'learning_object_file'
urlpatterns = [
    path('api/v1/learning-object-oer/', views.getDataNewLearningObject.as_view(), name='learningobject-oeradap'),
    path('api/v1/learning-object-oer/create', views.saveDataIntegrationWithOer.as_view(), name='learningobject-oeradap-create'),
]