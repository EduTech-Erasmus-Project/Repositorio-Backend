from applications.evaluation_student.models import (
    EvaluationQuestionQualification, 
    Guideline, 
    Principle, 
    Question, 
    StudentEvaluation,
    EvaluationPrincipleQualification,
    EvaluationGuidelineQualification,

)
from django.contrib import admin

# Register your models here.
admin.site.register(Principle)
admin.site.register(Guideline)
admin.site.register(Question)
admin.site.register(StudentEvaluation)
admin.site.register(EvaluationQuestionQualification)
admin.site.register(EvaluationPrincipleQualification)
admin.site.register(EvaluationGuidelineQualification)