from django.contrib import admin

# Register your models here.
from . models import (
    EvaluationConcept, 
    EvaluationQuestion,
    EvaluationConceptQualification,
    EvaluationQuestionsQualification,
    EvaluationCollaboratingExpert,
    #-nuevas tablas para el admin
    EvaluationMetadata,
    MetadataAutomaticEvaluation,
    MetadataQualificationConcept,
    MetadataSchemaQualification,
)

admin.site.register(EvaluationConcept)
admin.site.register(EvaluationQuestion)
admin.site.register(EvaluationConceptQualification)
admin.site.register(EvaluationQuestionsQualification)
admin.site.register(EvaluationCollaboratingExpert)
#-nuevas tablas para el admin
admin.site.register(EvaluationMetadata)
admin.site.register(MetadataAutomaticEvaluation)
admin.site.register(MetadataQualificationConcept)
admin.site.register(MetadataSchemaQualification)
