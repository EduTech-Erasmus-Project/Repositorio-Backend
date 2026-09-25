"""Modelos para la evaluación estudiantil de objetos de aprendizaje.

El módulo organiza la rúbrica en tres niveles jerárquicos:

- principios
- lineamientos asociados a cada principio
- preguntas asociadas a cada lineamiento

Sobre esa estructura se registran evaluaciones de estudiantes y promedios
agregados por principio, lineamiento y pregunta.
"""

from django.db import models
from model_utils.models import TimeStampedModel
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.user.models import User

class Principle(TimeStampedModel):
    """Principio general de la rúbrica de evaluación estudiantil."""

    principle = models.CharField(
        max_length=500,
        unique=True,
        blank=False,
        null=False,
        help_text="Nombre del principio principal de la rubrica de evaluacion estudiantil.",
    )
    def __str__(self):
        return self.principle

class Guideline(TimeStampedModel):
    """Lineamiento especifico que cuelga de un principio de evaluación."""

    guideline = models.CharField(
        max_length=1000,
        unique=True,
        blank=False,
        null=False,
        help_text="Texto del lineamiento que agrupa preguntas dentro de un principio.",
    )
    principle = models.ForeignKey(
        Principle,
        on_delete=models.CASCADE,
        related_name='guidelines',
        help_text="Principio al que pertenece este lineamiento.",
    )
    def __str__(self):
        return str(self.id)

class Question(TimeStampedModel):
    """Pregunta concreta de la rúbrica con metadata e intérpretes de respuesta.

    Conserva campos de interpretación y pesos heredados para convertir las
    respuestas del estudiante en puntajes comparables dentro del modelo.
    """

    question = models.CharField(
        max_length=1000,
        unique=True,
        blank=False,
        null=False,
        help_text="Texto de la pregunta que responde el estudiante al evaluar el OA.",
    )
    description = models.TextField(
        help_text="Descripcion o aclaracion para que el estudiante interprete la pregunta.",
    )
    metadata = models.TextField(
        help_text="Criterio o metadata de referencia asociado a la pregunta.",
    )
    ##########################################
    interpreter_st_yes = models.TextField(
        blank=True,
        null=True,
        help_text="Texto que explica como interpretar una respuesta afirmativa del estudiante.",
    )
    interpreter_st_no = models.TextField(
        blank=True,
        null=True,
        help_text="Texto que explica como interpretar una respuesta negativa del estudiante.",
    )
    interpreter_st_partially = models.TextField(
        blank=True,
        null=True,
        help_text="Texto que explica como interpretar una respuesta parcial del estudiante.",
    )
    interpreter_st_not_apply = models.TextField(
        blank=True,
        null=True,
        default='No aplica',
        help_text="Texto que explica cuando la pregunta no aplica para el OA evaluado.",
    )
    value_st_importance= models.FloatField(
        blank=True,
        null=True,
        default=0,
        help_text="Peso numerico de importancia usado al calcular la evaluacion estudiantil.",
    )
    #########################################
    #Peso y relevancia para cada pregunta
    relevance = models.CharField(
        max_length=50,
        blank=False,
        null=True,
        help_text="Nivel de relevancia textual o categorico asignado a la pregunta.",
    )
    weight = models.FloatField(
        blank=True,
        null=True,
        help_text="Ponderacion numerica de la pregunta dentro del lineamiento.",
    )

    guideline = models.ForeignKey(
        Guideline,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="Lineamiento al que pertenece la pregunta.",
    )
    def __str__(self):
        return str(self.id)


class StudentEvaluation(TimeStampedModel):
    """Cabecera de la evaluación que un estudiante realiza sobre un OA."""

    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        related_name='student_learning_objects',
        help_text="Objeto de aprendizaje evaluado por el estudiante.",
    )
    observation = models.TextField(
        blank=True,
        null=True,
        help_text="Comentario u observacion escrita por el estudiante durante la evaluacion.",
    )
    rating = models.FloatField(
        default=0.0,
        help_text="Calificacion general calculada o registrada para la evaluacion estudiantil.",
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_evaluation',
        help_text="Usuario estudiante que realizo la evaluacion.",
    )
    def __str__(self):
        return str(self.id)

class EvaluationPrincipleQualification(TimeStampedModel):
    """Promedio agregado por principio dentro de una evaluación estudiantil."""

    evaluation_principle = models.ForeignKey(
        Principle,
        on_delete=models.CASCADE,
        related_name='evaluation_principles',
        help_text="Principio evaluado dentro de una evaluacion estudiantil.",
    )
    evaluation_student = models.ForeignKey(
        StudentEvaluation,
        on_delete=models.CASCADE,
        related_name='evaluation_students',
        help_text="Evaluacion estudiantil a la que pertenece este promedio por principio.",
    )
    average_principle = models.FloatField(
        default=0.0,
        help_text="Promedio calculado para el principio dentro de la evaluacion estudiantil.",
    )
    def __str__(self):
        return str(self.id)

class EvaluationGuidelineQualification(TimeStampedModel):
    """Promedio agregado por lineamiento dentro de un principio evaluado."""

    guideline_pr = models.ForeignKey(
        Guideline,
        on_delete=models.CASCADE,
        related_name='guideline_pr',
        help_text="Lineamiento evaluado dentro del principio.",
    )
    principle_gl = models.ForeignKey(
        EvaluationPrincipleQualification,
        on_delete=models.CASCADE,
        related_name='principle_gl',
        help_text="Registro de promedio por principio al que pertenece este lineamiento.",
    )
    #evaluation_collaborating_expert = models.ForeignKey(EvaluationCollaboratingExpert,on_delete=models.CASCADE, related_name='concept_evaluations')
    average_guideline = models.FloatField(
        default=0.0,
        help_text="Promedio calculado para el lineamiento dentro del principio evaluado.",
    )
    def __str__(self):
        return str(self.id)

class EvaluationQuestionQualification(TimeStampedModel):
    """Respuesta y puntaje de una pregunta especifica en la evaluación estudiantil."""

    guideline_evaluations = models.ForeignKey(
        EvaluationGuidelineQualification,
        on_delete=models.CASCADE,
        related_name='guideline_evaluations',
        blank=True,
        null=True,
        help_text="Registro de promedio por lineamiento al que pertenece esta respuesta de pregunta.",
    )
    #student_evaluation = models.ForeignKey(StudentEvaluation,on_delete=models.CASCADE, related_name='studentevaluations')
    evaluation_question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='evaluation_questions',
        help_text="Pregunta de la rubrica estudiantil que fue calificada.",
    )
    qualification = models.FloatField(
        help_text="Valor numerico de la respuesta del estudiante para la pregunta.",
    )
    def __str__(self):
        return str(self.id)




