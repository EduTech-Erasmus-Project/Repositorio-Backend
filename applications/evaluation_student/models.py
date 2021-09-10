from django.db import models
from model_utils.models import TimeStampedModel
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.user.models import User

# Create your models here.
class Principle(TimeStampedModel):
    principle = models.CharField(max_length=500, unique=True,blank=False, null=False)
    def __str__(self):
        return self.principle

class Guideline(TimeStampedModel):
    guideline = models.CharField(max_length=1000, unique=True, blank=False, null=False)
    principle = models.ForeignKey(Principle, on_delete=models.CASCADE, related_name='guidelines')
    def __str__(self):
        return str(self.id)

class Question(TimeStampedModel):
    question = models.CharField(max_length=1000,unique=True, blank=False, null=False)
    description = models.TextField()
    metadata = models.TextField()
    ##########################################
    interpreter_st_yes = models.TextField(blank=True, null=True)
    interpreter_st_no = models.TextField(blank=True, null=True)
    interpreter_st_partially = models.TextField(blank=True, null=True)
    value_st_importance= models.FloatField(blank=True, null=True)
    #########################################
    guideline = models.ForeignKey(Guideline, on_delete=models.CASCADE, related_name='questions')
    def __str__(self):
        return str(self.id)


class StudentEvaluation(TimeStampedModel):
    learning_object = models.ForeignKey(LearningObjectMetadata,on_delete=models.CASCADE, related_name='student_learning_objects')
    observation = models.TextField(blank=True, null=True)
    rating = models.FloatField(default=0.0)
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_evaluation'
    )
    def __str__(self):
        return str(self.id)

#############NUEVOS MODELOS ESTUDIANTE

class EvaluationPrincipleQualification(TimeStampedModel):
    evaluation_principle = models.ForeignKey(Principle,on_delete=models.CASCADE, related_name='evaluation_principles')
    evaluation_student = models.ForeignKey(StudentEvaluation,on_delete=models.CASCADE, related_name='evaluation_students')
    average_principle = models.FloatField(default=0.0)
    def __str__(self):
        return str(self.id)

class EvaluationGuidelineQualification(TimeStampedModel):
    guideline_pr = models.ForeignKey(Guideline,on_delete=models.CASCADE, related_name='guideline_pr')
    principle_gl = models.ForeignKey(EvaluationPrincipleQualification,on_delete=models.CASCADE, related_name='principle_gl')
    #evaluation_collaborating_expert = models.ForeignKey(EvaluationCollaboratingExpert,on_delete=models.CASCADE, related_name='concept_evaluations')
    average_guideline = models.FloatField(default=0.0)
    def __str__(self):
        return str(self.id)

class EvaluationQuestionQualification(TimeStampedModel):
    guideline_evaluations = models.ForeignKey(EvaluationGuidelineQualification,on_delete=models.CASCADE, related_name='guideline_evaluations',blank=True, null=True)
    #student_evaluation = models.ForeignKey(StudentEvaluation,on_delete=models.CASCADE, related_name='studentevaluations')
    evaluation_question = models.ForeignKey(Question,on_delete=models.CASCADE, related_name='evaluation_questions')
    qualification = models.FloatField()
    def __str__(self):
        return str(self.id)





