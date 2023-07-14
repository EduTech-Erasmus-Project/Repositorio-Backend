from rest_framework.routers import DefaultRouter

from django.contrib import admin
from django.urls import path
from . import views


app_name = 'intearaction'
urlpatterns = [
    path('api/v1/learning-objects/liked/<int:pk>/', views.GetLikedLearningObjetById.as_view()),

    path('api/v1/learning-objects/most-liked/', views.MostLikeLearningObjects.as_view()),
    path('api/v1/learning-objects/liked-count/<int:pk>', views.LearingObjectLike.as_view()),
]