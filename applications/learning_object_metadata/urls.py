from rest_framework.routers import DefaultRouter

from django.contrib import admin
from django.urls import path
from . import views


app_name = 'learning_object_metadata'
urlpatterns = [
    path('api/v1/learning-object/<slug>/', views.SlugView.as_view(), name='slug'),
    path('api/v1/total-oa-approved/', views.TotalLearningObjectAproved.as_view()),
    path('api/v1/learning-objects/populars/', views.ListLearningObjectPopular.as_view()),
    path('api/v1/learning-objects/newsOas/', views.ListLearningObjectAlls.as_view()),
    path('api/v1/learning-objects/search/', views.SerachAPIView.as_view()),
    path('api/v1/learning-objects/search/expert/', views.SerachAPIViewExpert.as_view()),
    path('api/v1/learning-objects/comments/<pk>/', views.CommentaryListAPIView.as_view()),
    path('api/v1/learning-objects-approved-and-disapproved/<public>/', views.ListLearningObjectPublicAndPrivate.as_view()),
    path('api/v1/total-oa-approved-and-disapproved/', views.TotalLearningObjectAproved.as_view()),
    path('api/v1/learning-objects/evaluated-expert/<id>/', views.ListLearningObjectEvaluatedByExpert.as_view()),
    path('api/v1/learning-objects/evaluated-student/<id>/', views.ListLearningObjectEvaluatedByStudent.as_view()),
    path('api/v1/learning-objects/upload-teacher/<id>/', views.ListLearningObjectUploadByTeacher.as_view()),
    path('api/v1/learning-objects/years/', views.ListLearningObjecYears.as_view()),
    path('api/v1/learning-objects/viewed/', views.LearningObjectMetadataViewedAPIView.as_view()),
    path('api/v1/learning-objects/observation/', views.LearningObjectTecherListAPIView.as_view()),
    path('api/v1/learning-objects/my-qualification/', views.LearningObjectStudentQualificationAPIView.as_view()),
    path('api/v1/learning-objects-update-public/<int:pk>/', views.UpdatePublicLearningObject.as_view()),
]