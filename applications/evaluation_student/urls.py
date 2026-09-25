"""Rutas manuales del módulo de evaluación estudiantil.

Este archivo agrupa los endpoints que no salen del router principal, sobre
toda la entrega del formulario al estudiante y las consultas de resultados
públicos o privados por objeto de aprendizaje.
"""

from rest_framework.routers import DefaultRouter

from django.urls import path
from . import views


app_name = 'evaluation_student'
urlpatterns = [
    # Flujo del estudiante: rubrica y estado de evaluacion de OAs.
    path('api/v1/learning-objects-questions/student/', views.StudentQuestionAPIView.as_view(), name='question_students'),
    path('api/v1/learning-objects/student/rated/', views.LerningObjectRatedStudent.as_view(), name='rated'),
    path('api/v1/learning-objects/student/no-rated/', views.LerningObjectNotRatedStudent.as_view(), name='no_rated'),

    # Resultados de evaluacion del estudiante, tanto privados como publicos.
    path('api/v1/learning-objects/student/result-to-student/<int:pk>/', views.ListEvaluatedToStudentRetriveAPIView.as_view(), name='evaluated_to_student'),
    path('api/v1/learning-objects/student/result-to-public-student/<int:pk>/', views.ListEvaluatedToStudenPublicAPIView.as_view(), name='evaluated_to_public_student'),
    path('api/v1/learning-objects/student/result-to-public-student-single/<int:pk>/', views.ListEvaluatedStudentSinglePublicAPIView.as_view(), name='evaluated_to_public_student_single'),
]
