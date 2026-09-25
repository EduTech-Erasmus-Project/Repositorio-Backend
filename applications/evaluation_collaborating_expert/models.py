"""Modelos de evaluación experta para objetos de aprendizaje.

Este módulo define el dominio completo de la evaluación colaborativa:

- conceptos o áreas evaluadas
- preguntas y autoevaluaciones asociadas a cada concepto
- evaluaciones realizadas por expertos sobre un OA
- calificaciones agregadas por concepto y por pregunta
- esquemas usados por la evaluación automática de metadata
"""

from applications.evaluation_collaborating_expert.managers import EvaluationExpertManager
from applications.user.models import User
from model_utils.models import TimeStampedModel
from django.db import models
from django.conf import settings
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.learning_object_file.models import LearningObjectFile

class EvaluationConcept(TimeStampedModel):
    """Concepto o dimensión principal evaluada sobre un OA.

    Ejemplos típicos en este proyecto son accesibilidad, interactividad o
    características de percepción. De este concepto cuelgan preguntas,
    esquemas y agregados de calificación.
    """

    concept = models.CharField(
        max_length=500,
        unique=True,
        help_text="Nombre de la dimension o criterio principal que agrupa preguntas de evaluacion experta.",
    )
    def __str__(self):
        return self.concept

class SelfEvaluationQuestions(TimeStampedModel):
    """Pregunta de autoevaluación usada en el flujo de metadata automática.

    Estas preguntas sirven como puente entre un concepto de evaluación y los
    esquemas automáticos que luego se califican sobre el archivo OA.
    """

    description = models.CharField(
        max_length=500,
        unique=True,
        help_text="Texto de la pregunta de autoevaluacion mostrada al docente.",
    )
    descriptionEnglish = models.CharField(
        max_length=500,
        null=True,
        help_text="Version en ingles de la pregunta de autoevaluacion, usada por compatibilidad o exportacion.",
    )
    evaluation_concept = models.ForeignKey(
        EvaluationConcept,
        on_delete=models.CASCADE,
        related_name='evaluation_self_question_evaluations',
        null=True,
        help_text="Concepto de evaluacion al que pertenece la pregunta de autoevaluacion.",
    )
    def __str__(self):
        return self.description

class EvaluationQuestion(TimeStampedModel):
    """Pregunta experta individual asociada a un concepto de evaluación.

    Además del texto visible, el modelo conserva interpretes y pesos usados
    por el motor de evaluación para transformar respuestas en puntajes.
    """

    question = models.TextField(
        unique=True,
        help_text="Texto principal de la pregunta que responde el experto colaborador.",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Descripcion o aclaracion adicional para interpretar la pregunta experta.",
    )
    schema = models.TextField(
        blank=True,
        null=True,
        help_text="Referencia, criterio o esquema tecnico asociado a la pregunta.",
    )
    #######################################################################
    #Nuevos Campos para Inteprete de Preguntas y peso
    interpreter_yes = models.TextField(
        blank=True,
        null=True,
        help_text="Texto que explica como interpretar una respuesta afirmativa.",
    )
    interpreter_no = models.TextField(
        blank=True,
        null=True,
        help_text="Texto que explica como interpretar una respuesta negativa.",
    )
    interpreter_partially = models.TextField(
        blank=True,
        null=True,
        help_text="Texto que explica como interpretar una respuesta parcial.",
    )
    interpreter_not_apply = models.TextField(
        blank=True,
        null=True,
        default="No aplica",
        help_text="Texto que explica cuando la pregunta no aplica al OA evaluado.",
    )
    value_importance = models.FloatField(
        blank=True,
        null=True,
        default=0,
        help_text="Peso numerico de importancia usado al calcular la evaluacion de la pregunta.",
    )
    #######################################################################
    # Peso y relevancia para cada pregunta
    relevance = models.CharField(
        max_length=50,
        blank=False,
        null=True,
        help_text="Nivel de relevancia textual o categorico asignado a la pregunta.",
    )
    weight = models.FloatField(
        blank=True,
        null=True,
        help_text="Ponderacion numerica de la pregunta dentro del concepto evaluado.",
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Codigo corto unico usado para identificar la pregunta en administracion y reportes.",
    )
    evaluation_concept = models.ForeignKey(
        EvaluationConcept,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="Concepto de evaluacion al que pertenece la pregunta experta.",
    )
    def __str__(self):
        return self.question

class EvaluationCollaboratingExpert(TimeStampedModel):
    """evaluación completa emitida por un experto sobre un OA concreto.

    El flag `is_priority` identifica la evaluación experta que debe mostrarse
    como referencia principal cuando existen múltiples evaluaciones del mismo OA.
    """

    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        related_name='learning_objects',
        help_text="Objeto de aprendizaje evaluado por el experto colaborador.",
    )
    rating = models.FloatField(
        help_text="Calificacion general asignada al OA a partir de la evaluacion experta.",
    )
    is_priority = models.BooleanField(
        default=False,
        help_text="Marca la evaluacion experta que debe mostrarse como referencia principal del OA.",
    )
    observation = models.TextField(
        blank=True,
        null=True,
        help_text="Observacion textual del experto sobre la evaluacion realizada.",
    )
    collaborating_expert = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_evaluation',
        help_text="Usuario experto colaborador que registro la evaluacion.",
    )
    objects = EvaluationExpertManager()
    def __str__(self):
        return str(self.id)

class EvaluationConceptQualification(TimeStampedModel):
    """Promedio de calificación de un concepto dentro de una evaluación experta."""

    evaluation_concept = models.ForeignKey(
        EvaluationConcept,
        on_delete=models.CASCADE,
        related_name='evaluation_concept',
        help_text="Concepto evaluado dentro de una evaluacion experta.",
    )
    evaluation_collaborating_expert = models.ForeignKey(
        EvaluationCollaboratingExpert,
        on_delete=models.CASCADE,
        related_name='concept_evaluations',
        help_text="Evaluacion experta a la que pertenece este promedio por concepto.",
    )
    average = models.FloatField(
        default=0.0,
        help_text="Promedio calculado para el concepto dentro de la evaluacion experta.",
    )
    def __str__(self):
        return str(self.id)

class EvaluationQuestionsQualification(TimeStampedModel):
    """Calificación individual de una pregunta dentro de un concepto evaluado."""

    concept_evaluations = models.ForeignKey(
        EvaluationConceptQualification,
        on_delete=models.CASCADE,
        related_name='question_evaluations',
        blank=True,
        null=True,
        help_text="Registro de calificacion por concepto al que pertenece esta calificacion de pregunta",
    )
    evaluation_question = models.ForeignKey(
        EvaluationQuestion,
        on_delete=models.CASCADE,
        related_name='evaluation_questions',
        help_text="Pregunta experta calificada.",
    )
    qualification = models.FloatField(
        help_text="Valor numerico de la respuesta del experto para la pregunta.",
    )
    def __str__(self):
        return str(self.id)

######################-NUEVAS TABLAS-################################

class EvaluationMetadata(TimeStampedModel):
    """Esquema automático evaluable ligado a un concepto y a una auto-pregunta.

    Estos registros describen que fragmento de metadata debe buscarse y con
    que importancia pesa dentro de la evaluación automática del OA.
    """

    schema = models.TextField(
        blank=True,
        null=True,
        help_text="Ruta, clave o criterio de metadata que sera evaluado automaticamente.",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Descripcion del criterio automatico de metadata.",
    )
    value_importance_schema = models.FloatField(
        blank=True,
        null=True,
        help_text="Peso de importancia del schema dentro de la evaluacion automatica.",
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Codigo corto unico del criterio automatico de metadata.",
    )
    evaluation_concept = models.ForeignKey(
        EvaluationConcept,
        on_delete=models.CASCADE,
        related_name='schemas',
        help_text="Concepto de evaluacion al que pertenece este criterio automatico.",
    )
    self_evaluation_question = models.ForeignKey(
        SelfEvaluationQuestions,
        on_delete=models.SET_NULL,
        related_name='schemas_questions',
        null=True,
        help_text="Pregunta de autoevaluacion relacionada con el criterio automatico de metadata.",
    )
    def __str__(self):
        return self.schema

class MetadataAutomaticEvaluation(TimeStampedModel):
    """Resultado total de la evaluación automática de metadata para un OA."""

    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        related_name='metadata_learning_objects',
        help_text="Objeto de aprendizaje al que pertenece la evaluacion automatica de metadata.",
    )
    rating_schema = models.FloatField(
        help_text="Calificacion total obtenida por el OA en la evaluacion automatica de metadata.",
    )
    def __str__(self):
        return str(self.id)

class MetadataQualificationConcept(TimeStampedModel):
    """Promedio automático obtenido por concepto dentro de un OA evaluado."""

    evaluation_concept = models.ForeignKey(
        EvaluationConcept,
        on_delete=models.CASCADE,
        related_name='evaluation_automatic_evaluations',
        help_text="Concepto evaluado automaticamente desde metadata.",
    )
    evaluation_automatic_evaluation = models.ForeignKey(
        MetadataAutomaticEvaluation,
        on_delete=models.CASCADE,
        related_name='metadata_concept_evaluations',
        help_text="Evaluacion automatica total a la que pertenece este promedio por concepto.",
    )
    average_schema = models.FloatField(
        default=0.0,
        help_text="Promedio automatico calculado para el concepto.",
    )
    def __str__(self):
        return str(self.id)

class MetadataSchemaQualification(TimeStampedModel):
    """Calificación individual de un esquema automático de metadata."""

    evaluation_metadata = models.ForeignKey(
        MetadataQualificationConcept,
        on_delete=models.CASCADE,
        related_name='metadata_evaluations',
        blank=True,
        null=True,
        help_text="Registro de promedio automatico por concepto al que pertenece esta calificacion de schema; en base de datos se guarda su id.",
    )
    evaluation_schema = models.ForeignKey(
        EvaluationMetadata,
        on_delete=models.CASCADE,
        related_name='evaluation_schemas',
        help_text="Criterio automatico de metadata que fue calificado.",
    )
    qualification = models.FloatField(
        help_text="Valor numerico obtenido por el criterio automatico de metadata.",
    )
    def __str__(self):
        return str(self.id)

class MetadataSchemaQuestionQualification(TimeStampedModel):
    """Respuesta de autoevaluación por archivo OA y pregunta asociada.

    Esta tabla se usa como insumo previo para derivar la evaluación automática
    cuando el OA pasa por el flujo de integración/adaptación.
    """

    self_evaluation_question = models.ForeignKey(
        SelfEvaluationQuestions,
        on_delete= models.CASCADE,
        related_name='self_questions_qualifications',
        help_text="Pregunta de autoevaluacion respondida durante el flujo del OA.",
    )
    qualification = models.FloatField(
        default=0.0,
        help_text="Valor numerico derivado de la respuesta de autoevaluacion.",
    )
    learning_object_file = models.ForeignKey(
        LearningObjectFile,
        on_delete=models.CASCADE,
        related_name='metadata_schema_question_learning_objects',
        help_text="Archivo OA al que pertenece la respuesta de autoevaluacion.",
    )
    def __str__(self):
        return str(self.id)
