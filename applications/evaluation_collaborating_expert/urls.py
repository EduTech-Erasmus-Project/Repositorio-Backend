"""Rutas manuales del módulo de evaluación colaborativa experta.

Este archivo concentra endpoints que no salen del `DefaultRouter`, sobre todo
consultas de resultados, listados para expertos y relaciones auxiliares entre
schemas de metadata y auto-preguntas.
"""

from rest_framework.routers import DefaultRouter

from django.urls import path
from . import views


app_name = 'evaluation_collaborating_expert'
urlpatterns = [
    # Flujo del experto colaborador: catálogo de preguntas y estado de evaluación.
    path('api/v1/learning-objects-questions/expert/', views.EvaluationQuestionsExpertView.as_view(), name='question_teachers'),
    path('api/v1/learning-objects/expert-collaborator/rated/', views.LerningObjectRated.as_view(), name='rated'),
    path('api/v1/learning-objects/expert-collaborator/no-rated/', views.LerningObjectNotRated.as_view(), name='no_rated'),

    # Resultados de evaluación por OA para vistas públicas y privadas.
    path('api/v1/learning-objects/evaluations-result-expert/<int:pk>/', views.ListOAEvaluatedRetriveAPIView.as_view(), name='evaluated'),
    path('api/v1/learning-objects/evaluations-result-expert-priority/<int:pk>/', views.ListOAEvaluatedPriorityRetriveAPIView.as_view(), name='evaluated'),
    path('api/v1/learning-objects/evaluations-result-expert-single/<int:pk>/', views.ListOAEvaluatedRetriveAPIViewSingleUser.as_view(), name='evaluated_single'),
    path('api/v1/learning-objects/evaluations-result-to-expert/<int:pk>/', views.ListOAEvaluatedToExpertRetriveAPIView.as_view(), name='evaluated_to_expert'),
    path('api/v1/learning-objects/evaluations-result-to-expert-automatic/<int:pk>/', views.ListOAEvaluatedToAutomaticAPIView.as_view(), name='evaluated_to_expert-automatic'),

    # Relaciones auxiliares entre metadata automática y auto-preguntas.
    path('api/v1/learning-objects/add-metadata-question-relationship/<int:pk>', views.RelationshipBetweenMetadataQuestion.as_view(), name="relationship_metadata_question_delete"),
    path('api/v1/learning-objects/add-metadata-question-relationship/', views.RelationshipBetweenMetadataQuestion.as_view(), name="relationship_metadata_question"),
    path('api/v1/learning-objects/add-metadata-self-question', views.CreateMetadataAssessmentSelfQuestion.as_view(), name="create_metadata_self_question"),

    # Borrado legacy fuera del router principal de schemas.
    path('api/v1/learning-objects/object-learning-question-evaluation-schema-delete/<int:pk>', views.DeleteSelfEvaluationGenegircView.as_view(), name='evaluation_question_schema_delete')
]
