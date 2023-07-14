from rest_framework.routers import DefaultRouter

from django.urls import path
from . import views


app_name = 'evaluation_collaborating_expert'
urlpatterns = [
    path('api/v1/learning-objects-questions/expert/', views.EvaluationQuestionsExpertView.as_view(), name='question_teachers'),
    path('api/v1/learning-objects/expert-collaborator/rated/', views.LerningObjectRated.as_view(), name='rated'),
    path('api/v1/learning-objects/expert-collaborator/no-rated/', views.LerningObjectNotRated.as_view(), name='no_rated'),
    path('api/v1/learning-objects/evaluations-result-expert/<pk>/', views.ListOAEvaluatedRetriveAPIView.as_view(), name='evaluated'),
    path('api/v1/learning-objects/evaluations-result-expert-priority/<pk>/', views.ListOAEvaluatedPriorityRetriveAPIView.as_view(), name='evaluated'),
    path('api/v1/learning-objects/evaluations-result-expert-single/<pk>/', views.ListOAEvaluatedRetriveAPIViewSingleUser.as_view(), name='evaluated_single'),
    path('api/v1/learning-objects/evaluations-result-to-expert/<pk>/', views.ListOAEvaluatedToExpertRetriveAPIView.as_view(), name='evaluated_to_expert'),
    path('api/v1/learning-objects/evaluations-result-to-expert-automatic/<pk>/', views.ListOAEvaluatedToAutomaticAPIView.as_view(), name='evaluated_to_expert-automatic'),

    path('api/v1/learning-objects/add-metadata-question-relationship/<pk>', views.RelationshipBetweenMetadataQuestion.as_view(), name="relationship_metadata_question_delete"),
    path('api/v1/learning-objects/add-metadata-question-relationship/', views.RelationshipBetweenMetadataQuestion.as_view(), name="relationship_metadata_question"),
    path('api/v1/learning-objects/add-metadata-self-question', views.CreateMetadataAssessmentSelfQuestion.as_view(), name="create_metadata_self_question"),

    path('api/v1/learning-objects/object-learning-question-evaluation-schema-delete/<pk>', views.DeleteSelfEvaluationGenegircView.as_view(), name='evaluation_question_schema_delete')
]