from applications.evaluation_collaborating_expert.managers import EvaluationExpertManager
from applications.user.models import User
from model_utils.models import TimeStampedModel
from django.db import models
from django.conf import settings
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.learning_object_file.models import LearningObjectFile

class EvaluationConcept(TimeStampedModel):
    concept = models.CharField(max_length=500, unique=True)
    def __str__(self):
        return self.concept

class SelfEvaluationQuestions(TimeStampedModel):
    description = models.CharField(max_length=500, unique=True)
    descriptionEnglish = models.CharField(max_length=500, null=True)
    evaluation_concept = models.ForeignKey(EvaluationConcept, on_delete=models.CASCADE,related_name='evaluation_self_question_evaluations', null=True)
    def __str__(self):
        return self.description

class EvaluationQuestion(TimeStampedModel):
    question = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    schema = models.TextField(blank=True, null=True)
    #######################################################################
    #Nuevos Campos para Inteprete de Preguntas y peso
    interpreter_yes = models.TextField(blank=True, null=True)
    interpreter_no = models.TextField(blank=True, null=True)
    interpreter_partially = models.TextField(blank=True, null=True)
    interpreter_not_apply = models.TextField(blank=True, null=True)
    value_importance = models.FloatField(blank=True, null=True)
    #######################################################################
    # Peso y relevancia para cada pregunta
    relevance = models.CharField(max_length=50, blank=False, null=True)
    weight = models.FloatField(blank=True, null=True)

    code = models.CharField(max_length=10, unique=True)
    evaluation_concept = models.ForeignKey(EvaluationConcept,on_delete=models.CASCADE, related_name='questions')
    def __str__(self):
        return self.question

class EvaluationCollaboratingExpert(TimeStampedModel):
    learning_object = models.ForeignKey(LearningObjectMetadata,on_delete=models.CASCADE, related_name='learning_objects')
    rating = models.FloatField()
    is_priority = models.BooleanField(default=False)
    observation = models.TextField(blank=True, null=True)
    collaborating_expert = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_evaluation'
    )
    objects = EvaluationExpertManager()
    def __str__(self):
        return str(self.id)

class EvaluationConceptQualification(TimeStampedModel):
    evaluation_concept = models.ForeignKey(EvaluationConcept,on_delete=models.CASCADE, related_name='evaluation_concept')
    evaluation_collaborating_expert = models.ForeignKey(EvaluationCollaboratingExpert,on_delete=models.CASCADE, related_name='concept_evaluations')
    average = models.FloatField(default=0.0)
    def __str__(self):
        return str(self.id)

class EvaluationQuestionsQualification(TimeStampedModel):
    concept_evaluations = models.ForeignKey(EvaluationConceptQualification,on_delete=models.CASCADE, related_name='question_evaluations',blank=True, null=True)
    evaluation_question = models.ForeignKey(EvaluationQuestion,on_delete=models.CASCADE, related_name='evaluation_questions')
    qualification = models.FloatField()
    def __str__(self):
        return str(self.id)

######################-NUEVAS TABLAS-################################

#Tabla de Metadatos Automaticos Para Evaluacion
class EvaluationMetadata(TimeStampedModel):
    schema = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    value_importance_schema = models.FloatField(blank=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    evaluation_concept = models.ForeignKey(EvaluationConcept,on_delete=models.CASCADE, related_name='schemas')
    self_evaluation_question = models.ForeignKey(SelfEvaluationQuestions, on_delete=models.SET_NULL, related_name='schemas_questions', null=True)
    def __str__(self):
        return self.schema

#Tabla de Raiting total del objeto de aprendizaje
class MetadataAutomaticEvaluation(TimeStampedModel):
    learning_object = models.ForeignKey(LearningObjectMetadata,on_delete=models.CASCADE, related_name='metadata_learning_objects')
    rating_schema = models.FloatField()
    def __str__(self):
        return str(self.id)

#Tabla de Calificacion para cada concepto o area
class MetadataQualificationConcept(TimeStampedModel):
    evaluation_concept = models.ForeignKey(EvaluationConcept,on_delete=models.CASCADE, related_name='evaluation_automatic_evaluations')
    evaluation_automatic_evaluation = models.ForeignKey(MetadataAutomaticEvaluation,on_delete=models.CASCADE, related_name='metadata_concept_evaluations')
    average_schema = models.FloatField(default=0.0)
    def __str__(self):
        return str(self.id)

#Tabla de Califiacion de cada metadato
class MetadataSchemaQualification(TimeStampedModel):
    evaluation_metadata = models.ForeignKey(MetadataQualificationConcept,on_delete=models.CASCADE, related_name='metadata_evaluations',blank=True, null=True)
    evaluation_schema = models.ForeignKey(EvaluationMetadata,on_delete=models.CASCADE, related_name='evaluation_schemas')
    qualification = models.FloatField()
    def __str__(self):
        return str(self.id)

class MetadataSchemaQuestionQualification(TimeStampedModel):
    self_evaluation_question = models.ForeignKey(SelfEvaluationQuestions, on_delete= models.CASCADE, related_name='self_questions_qualifications')
    qualification = models.FloatField(default=0.0)
    learning_object_file = models.ForeignKey(LearningObjectFile, on_delete=models.CASCADE,related_name='metadata_schema_question_learning_objects')
    def __str__(self):
        return str(self.id)
