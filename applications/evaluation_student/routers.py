"""Recursos expuestos por router en evaluación estudiantil.

Aqui viven los CRUD y acciones principales del módulo. Las rutas manuales de
formulario y resultados públicos/privados permanecen en `urls.py`.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Captura principal de evaluaciones estudiantiles.
router.register(r'api/v1/learning-objects/student-evaluation', views.StudentEvaluationView, basename='evaluation_student')

# Lectura administrativa de la estructura de lineamientos y preguntas.
router.register(r'api/v1/object-learning-concept-evaluation-student-questions', views.EvaluationPrincipleGuidelienViewSet, basename='student_list')

# CRUD de preguntas de la rúbrica.
router.register(r'api/v1/learning-objective-assessment-student', views.EvaluationQuestionsStudentViewSet, basename='create_question')

# CRUD de principios y lineamientos de la rúbrica.
router.register(r'api/v1/learning-objects/student-register-principles', views.EvaluationPrincipleRegisterViewSet, basename='register-principles')
router.register(r'api/v1/learning-objects/student-register-guideline', views.EvaluationGuidelineRegisterViewSet, basename='register-guideline')

urlpatterns = router.urls
