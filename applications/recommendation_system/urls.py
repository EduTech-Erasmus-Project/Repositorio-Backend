from django.urls import path
from . import views
from rest_framework_simplejwt import views as jwt_views


app_name = 'recommendation_system'
urlpatterns = [
    path('api/v1/learning-objects/recommended/', views.LearningObjectRecommended.as_view()),
    # path('api/v1/dataset-generator/', views.DataSetGeneratorView.as_view(), name='student_list'),
]