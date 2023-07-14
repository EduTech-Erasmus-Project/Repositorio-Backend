from rest_framework.routers import DefaultRouter

from django.urls import path
from . import views


app_name = 'evaluation_student'
urlpatterns = [
    path('api/v1/learning-objects-questions/student/', views.StudentQuestionAPIView.as_view(), name='question_students'),
    path('api/v1/learning-objects/student/rated/', views.LerningObjectRatedStudent.as_view(), name='rated'),
    path('api/v1/learning-objects/student/no-rated/', views.LerningObjectNotRatedStudent.as_view(), name='no_rated'),

    path('api/v1/learning-objects/student/result-to-student/<pk>/', views.ListEvaluatedToStudentRetriveAPIView.as_view(), name='evaluated_to_student'),
    path('api/v1/learning-objects/student/result-to-public-student/<pk>/', views.ListEvaluatedToStudenPublicAPIView.as_view(), name='evaluated_to_public_student'),
    path('api/v1/learning-objects/student/result-to-public-student-single/<pk>/', views.ListEvaluatedStudentSinglePublicAPIView.as_view(), name='evaluated_to_public_student_single'),
]