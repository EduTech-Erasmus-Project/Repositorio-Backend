"""Rutas manuales del módulo de metadata de objetos de aprendizaje.

Este archivo agrupa endpoints que no encajan en el router principal del módulo:

- buscadores públicos y para expertos
- listados de destacados, años y observaciones
- flujos administrativos de aprobación y revisión
- resultados de evaluaciones por estudiante o experto
"""

from django.urls import path

from . import views


app_name = "learning_object_metadata"

urlpatterns = [
    # Detalle y catálogos públicos.
    path("api/v1/learning-object/<slug>/", views.SlugView.as_view(), name="slug"),
    path("api/v1/total-oa-approved/", views.TotalLearningObjectAproved.as_view()),
    path("api/v1/learning-objects/populars/", views.ListLearningObjectPopular.as_view()),
    path("api/v1/learning-objects/newsOas/", views.ListLearningObjectAlls.as_view()),
    path("api/v1/learning-objects/search/", views.SerachAPIView.as_view()),
    path("api/v1/learning-objects/search/expert/", views.SerachAPIViewExpert.as_view()),
    path("api/v1/learning-objects/comments/<pk>/", views.CommentaryListAPIView.as_view()),
    path("api/v1/learning-objects/years/", views.ListLearningObjecYears.as_view()),
    path("api/v1/learning-objects-most-recent/", views.learningObjectsTheMostRecent.as_view()),

    # Revisión administrativa de aprobación y carga docente.
    path(
        "api/v1/learning-objects-approved-and-disapproved/<public>/",
        views.ListLearningObjectPublicAndPrivate.as_view(),
    ),
    path("api/v1/total-oa-approved-and-disapproved/", views.TotalLearningObjectAproved.as_view()),
    path("api/v1/learning-objects/upload-teacher/<id>/", views.ListLearningObjectUploadByTeacher.as_view()),
    path("api/v1/learning-objects-update-public/<int:pk>/", views.UpdatePublicLearningObject.as_view()),
    path("api/v1/learning-objects-review-notification/<int:pk>/", views.LearningObjectReviewNotificationAPIView.as_view()),

    # Resultados de evaluación experta y estudiantil.
    path("api/v1/learning-objects/evaluated-expert/<id>", views.ListLearningObjectEvaluatedByExpert.as_view()),
    path(
        "api/v1/learning-objects/evaluated-expert-update/<pk>",
        views.ListLearningObjectExpertQualificationsUpdate.as_view(),
    ),
    path("api/v1/learning-objects/evaluated-student/<id>", views.ListLearningObjectEvaluatedByStudent.as_view()),
    path(
        "api/v1/learning-objects/evaluated-expert-qualification/<id>",
        views.ListLearningObjectEvaluatedByExpertQualifications.as_view(),
    ),
    path(
        "api/v1/learning-objects/evaluated-student-qualification/<id>",
        views.ListLearningObjectEvaluatedByStudentQualification.as_view(),
    ),
    path(
        "api/v1/learning-objects/evaluated-student-qualification-results/<user>/<id>",
        views.ListEvaluatedToStudentRetriveAPIView.as_view(),
    ),
    path(
        "api/v1/learning-objects/evaluated-expert-qualification-results/<user>/<id>",
        views.ListOAEvaluatedToExpertRetriveAPIView.as_view(),
    ),

    # Historiales y listados asociados al usuario autenticado.
    path("api/v1/learning-objects/viewed/", views.LearningObjectMetadataViewedAPIView.as_view()),
    path("api/v1/learning-objects/observation/", views.LearningObjectTecherListAPIView.as_view()),
    path("api/v1/learning-objects/my-qualification/", views.LearningObjectStudentQualificationAPIView.as_view()),
]
