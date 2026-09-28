"""Serializers para CRUD, evaluación experta y evaluación automática.

Este módulo mezcla serializers de varios flujos históricos:

- mantenimiento de conceptos, preguntas y esquemas
- captura de evaluaciones expertas sobre un OA
- consultas enriquecidas para paneles administrativos
- resultados de evaluación automática de metadata
"""

from drf_spectacular.utils import extend_schema_field
from django.db.models.base import Model
from applications.learning_object_metadata.utils import get_rating_value
from applications.knowledge_area.serializers import KnowledgeAreaListSerializer
from applications.education_level.serializers import EducationLevelListSerializer
from applications.learning_object_file.serializers import LearningObjectSerializer
from applications.license.serializers import LicenseSerializer
from roabackend.settings import CALIFICATION_OPTIONS, YES, NO, NOT_APPLY
from django.db.models.aggregates import Avg
from rest_framework.validators import UniqueValidator
from applications.learning_object_metadata.models import LearningObjectMetadata
from rest_framework import fields, serializers
from .models import (
    EvaluationConcept,
    EvaluationMetadata,
    EvaluationQuestion,
    EvaluationQuestionsQualification,
    EvaluationConceptQualification,
    EvaluationCollaboratingExpert,
    MetadataAutomaticEvaluation,
    MetadataQualificationConcept,
    MetadataSchemaQualification,
SelfEvaluationQuestions
)
from applications.evaluation_collaborating_expert import models
from ..user.serializers import UserCommentSerializer


class EvaluationQuestionRegisterSerializer(serializers.Serializer):
    """Payload de alta para preguntas expertas con intérpretes y pesos."""

    """question = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=EvaluationQuestion.objects.all(),
        message="Esta pregunta ya esta registrado.",
        )])"""
    question = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    schema = serializers.CharField(required=True)
    ###################################################
    interpreter_yes = serializers.CharField(required=True)
    interpreter_no = serializers.CharField(required=True)
    interpreter_partially = serializers.CharField(required=True)
    interpreter_not_apply = serializers.CharField(required=True)
    value_importance = serializers.CharField(required=True)

    weight = serializers.CharField(required=True)
    relevance = serializers.CharField(required=True)
    ###################################################
    """code = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=EvaluationQuestion.objects.all(),
        message="Este código ya esta registrado.",
        )])"""
    code = serializers.CharField(required=True)
    # evaluation_concept = serializers.IntegerField(required=True)


class EvaluationQuestionSerializer(serializers.ModelSerializer):
    """Serializer CRUD directo del modelo `EvaluationQuestion`."""

    class Meta:
        model = EvaluationQuestion
        fields = ('__all__')


class EvaluationQuestionListSerializer(serializers.ModelSerializer):
    """Salida de lectura para preguntas incluyendo intérpretes y ponderación."""

    class Meta:
        model = EvaluationQuestion
        # nuevo datos intérprete 
        fields = (
            'id',
            'question',
            'description',
            'schema',
            'code',
            'interpreter_yes',
            'interpreter_no',
            'interpreter_partially',
            'interpreter_not_apply',
            'value_importance',
            'relevance',
            'weight'
        )


class EvaluationConceptSerializer(serializers.ModelSerializer):
    """Serializer mínimo de concepto de evaluación."""

    class Meta:
        model = EvaluationConcept
        fields = ['concept']

class EvaluationSelfQuestionSerializer(serializers.ModelSerializer):
    """Serializer CRUD de preguntas de autoevaluación."""

    class Meta:
        model = SelfEvaluationQuestions
        fields = ['description','descriptionEnglish','evaluation_concept']

class EvaluationConceptListSerializer(serializers.ModelSerializer):
    """Lista conceptos con sus preguntas expertas ya anidadas."""

    questions = EvaluationQuestionListSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluationConcept
        fields = ['id', 'concept', 'questions']


class EvaluationQuestionQualificationSerializer(serializers.ModelSerializer):
    """Calificación de pregunta con la etiqueta visible de respuesta."""

    evaluation_question = EvaluationQuestionListSerializer(read_only=True)
    qualification = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationQuestionsQualification
        ref_name = 'ExpertEvaluationQuestionQualification'
        fields = (
            'id',
            'qualification',
            'evaluation_question'
        )

    @extend_schema_field(serializers.CharField())
    def get_qualification(self, obj) -> str:
        """Convierte el valor numérico a la opción visible del frontend."""

        if obj.qualification is not None and float(YES) == float(obj.qualification):
            return CALIFICATION_OPTIONS['YES']
        elif obj.qualification is not None and float(NO) == float(obj.qualification):
            return CALIFICATION_OPTIONS['NO']
        elif obj.qualification is not None and float(obj.qualification) == float(NOT_APPLY):
            return CALIFICATION_OPTIONS['NOT_APPLY']
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']


class QuestionQualificationListSerializer(serializers.ModelSerializer):
    """Detalle expandido de una pregunta evaluada dentro de un concepto."""

    question = serializers.SerializerMethodField()
    question_id = serializers.SerializerMethodField()
    qualification = serializers.SerializerMethodField()
    interpreter_yes = serializers.SerializerMethodField()
    interpreter_no = serializers.SerializerMethodField()
    interpreter_partially = serializers.SerializerMethodField()
    interpreter_not_apply = serializers.SerializerMethodField()
    schema = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationQuestionsQualification
        fields = (
            'id',
            'question_id',
            'question',
            'schema',
            'qualification',
            'interpreter_yes',
            'interpreter_no',
            'interpreter_partially',
            'interpreter_not_apply',
        )

    @extend_schema_field(serializers.CharField())
    def get_schema(self, obj) -> str:
        """Devuelve el esquema asociado a la pregunta evaluada."""

        query = EvaluationQuestion.objects.filter(pk=obj.evaluation_question.id).values('schema')
        if query.exists():
            return query[0]['schema']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_interpreter_yes(self, obj) -> str:
        """Devuelve el texto interpretativo para la opción afirmativa."""

        query = EvaluationQuestion.objects.filter(pk=obj.evaluation_question.id).values('interpreter_yes')
        if query.exists():
            return query[0]['interpreter_yes']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_interpreter_no(self, obj) -> str:
        """Devuelve el texto interpretativo para la opción negativa."""

        query = EvaluationQuestion.objects.filter(pk=obj.evaluation_question.id).values('interpreter_no')
        if query.exists():
            return query[0]['interpreter_no']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_interpreter_partially(self, obj) -> str:
        """Devuelve el texto interpretativo para la opción parcial."""

        query = EvaluationQuestion.objects.filter(pk=obj.evaluation_question.id).values('interpreter_partially')
        if query.exists():
            return query[0]['interpreter_partially']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_interpreter_not_apply(self, obj) -> str:
        """Devuelve el texto interpretativo para la opción no aplica."""

        query = EvaluationQuestion.objects.filter(pk=obj.evaluation_question.id).values('interpreter_not_apply')
        if query.exists():
            return query[0]['interpreter_not_apply']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_question(self, obj) -> str:
        """Expone el texto de la pregunta evaluada."""

        query = EvaluationQuestion.objects.filter(pk=obj.evaluation_question.id).values('question')
        if query.exists():
            return query[0]['question']
        else:
            return ""

    @extend_schema_field(serializers.IntegerField())
    def get_question_id(self, obj) -> int:
        return obj.evaluation_question.id

    @extend_schema_field(serializers.CharField())
    def get_qualification(self, obj) -> str:
        """Convierte el valor numerico a la opción visible del frontend."""

        if obj.qualification is not None and float(YES) == float(obj.qualification):
            return CALIFICATION_OPTIONS['YES']
        elif obj.qualification is not None and float(NO) == float(obj.qualification):
            return CALIFICATION_OPTIONS['NO']
        elif obj.qualification is not None and float(obj.qualification) == float(NOT_APPLY):
            return CALIFICATION_OPTIONS['NOT_APPLY']
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']


class LearningObjectMetadataSerializer(serializers.ModelSerializer):
    """Referencia mínima al OA evaluado."""

    class Meta:
        model = LearningObjectMetadata
        fields = (
            'id',
            'general_title'
        )


class LearningObjectMetadataSearchSerializer(serializers.ModelSerializer):
    """Lectura expandida del OA para pantallas de consulta y búsqueda."""

    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    education_levels = EducationLevelListSerializer(read_only=True)
    knowledge_area = KnowledgeAreaListSerializer()
    user_created = UserCommentSerializer(read_only=True)

    class Meta:
        model = LearningObjectMetadata
        fields = ('__all__')


class EvaluationConceptQualificationSerializer(serializers.ModelSerializer):
    """Detalle de un concepto evaluado con sus preguntas calificadas."""

    evaluation_concept = EvaluationConceptSerializer()
    question_evaluations = EvaluationQuestionQualificationSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluationConceptQualification
        fields = (
            'id',
            'evaluation_concept',
            'question_evaluations'
        )


class EvaluationCollaboratingExpertSerializer(serializers.ModelSerializer):
    """evaluación experta completa con conceptos ya expandidos."""

    concept_evaluations = EvaluationConceptQualificationSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluationCollaboratingExpert
        fields = (
            'id',
            'learning_object',
            'rating', 'observation',
            'concept_evaluations'
        )


class EvaluationCollaboratingExpertSearchSerializer(serializers.ModelSerializer):
    """Salida reducida para resultados de búsqueda centrados en el OA."""

    learning_object = LearningObjectMetadataSearchSerializer(read_only=True)

    class Meta:
        model = EvaluationCollaboratingExpert
        fields = ('learning_object',)


class EvaluationCollaboratingExpertAllSerializer(serializers.ModelSerializer):
    """Serializer CRUD directo del modelo `EvaluationCollaboratingExpert`."""

    class Meta:
        model = EvaluationCollaboratingExpert
        fields = ('__all__')


class EvaluationConceptQualificationsValueSerializer(serializers.ModelSerializer):
    """Concepto evaluado mostrando promedio visible y preguntas expandidas."""

    evaluation_concept = EvaluationConceptSerializer()
    question_evaluations = QuestionQualificationListSerializer(many=True, read_only=True)
    average = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationConceptQualification
        fields = (
            'evaluation_concept',
            'average',
            'question_evaluations',
        )

    @extend_schema_field(serializers.IntegerField())
    def get_average(self, obj) -> float:
        """Normaliza el promedio interno a la escala visible del sistema."""

        return get_rating_value(obj.average)


class EvaluationCollaboratingExpertEvaluationSerializer(serializers.ModelSerializer):
    """Detalle de evaluación experta mostrado en resultados administrativos."""

    concept_evaluations = EvaluationConceptQualificationsValueSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluationCollaboratingExpert
        fields = (
            'id',
            'observation',
            'learning_object',
            'concept_evaluations',
        )


class ArrayIntegerSerializer(serializers.ListField):
    """Lista tipada de enteros para payloads compactos."""

    children = serializers.IntegerField(required=True)


class ArrayStringSerializer(serializers.ListField):
    """Lista tipada de cadenas para payloads compactos."""

    children = serializers.CharField(required=True)


class ArrayFloatSerializer(serializers.ListField):
    """Lista tipada de flotantes para payloads compactos."""

    children = serializers.FloatField(required=True)


class ArrayDicFielSerializer(serializers.ListField):
    """Lista de diccionarios usada para respuestas expertas por pregunta."""

    children = serializers.DictField(required=True)


class EvaluationExpertCreateSerializer(serializers.Serializer):
    """Payload de creación de una evaluación experta sobre un OA."""

    learning_object = serializers.IntegerField(required=True)
    results = ArrayDicFielSerializer()
    observation = serializers.CharField(required=False)

    def validate(self, data):
        """Valida existencia del OA, preguntas y opciónes de respuesta."""

        incident = LearningObjectMetadata.objects.filter(pk=int(data['learning_object']))
        if not incident:
            raise serializers.ValidationError(f"Not exist oa with code {int(data['learning_object'])}")
        for value in data['results']:
            if not EvaluationQuestion.objects.filter(pk=value['id']).exists():
                raise serializers.ValidationError(f"Not exist question with pk {value['id']}")
        for option in data['results']:
            if option['value'] != CALIFICATION_OPTIONS['YES'] and option['value'] != CALIFICATION_OPTIONS['NO'] and \
                    option['value'] != CALIFICATION_OPTIONS['PARTIALLY'] and option['value'] != CALIFICATION_OPTIONS[
                'NOT_APPLY']:
                raise serializers.ValidationError(f"Options are Si, No, Parcialmente and No aplica")
        return data


class LearningObjectMetadataSearchSerializer(serializers.ModelSerializer):
    """Duplicado heredado del serializer de búsqueda de OA.

    Se mantiene por compatibilidad con el resto del módulo, que lo referencia
    mas abajo sin importar la definición previa del mismo nombre.
    """

    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    education_levels = EducationLevelListSerializer(read_only=True)
    knowledge_area = KnowledgeAreaListSerializer()
    user_created = UserCommentSerializer(read_only=True)

    class Meta:
        model = LearningObjectMetadata
        fields = ('__all__')


class EvaluationCollaboratingExpertSearchSerializer(serializers.ModelSerializer):
    """Duplicado heredado del serializer de búsqueda de evaluación experta."""

    learning_object = LearningObjectMetadataSearchSerializer(read_only=True)

    class Meta:
        model = EvaluationCollaboratingExpert
        fields = ('learning_object',)


class EvaluationConceptSearchSerializer(serializers.ModelSerializer):
    """Salida mínima para buscar conceptos a partir de una evaluación experta."""

    evaluation_collaborating_expert = EvaluationCollaboratingExpertSearchSerializer(read_only=True)

    class Meta:
        model = EvaluationConceptQualification
        fields = (
            'evaluation_collaborating_expert',
        )


class QuestionQualificationSearchSerializer(serializers.ModelSerializer):
    """Salida mínima para buscar OAs evaluados desde sus preguntas."""

    concept_evaluations = EvaluationConceptSearchSerializer(read_only=True)

    class Meta:
        model = EvaluationQuestionsQualification
        fields = ('concept_evaluations',)


class EvaluationSchemaListSerializer(serializers.ModelSerializer):
    """Lectura de esquemas de metadata evaluables dentro de un concepto."""

    class Meta:
        model = EvaluationMetadata
        ref_name = 'ExpertEvaluationSchemaList'
        fields = ('id', 'schema', 'description', 'value_importance_schema', 'code','evaluation_concept')


class EvaluationConceptListSerializerSCHEMA(serializers.ModelSerializer):
    """Conceptos con sus esquemas de metadata ya anidados."""

    schemas = EvaluationSchemaListSerializer(many=True, read_only=True)
    class Meta:
        model = EvaluationConcept
        fields = ['id', 'concept', 'schemas']

class EvaluationSelfQuestionListSerializerSCHEMA(serializers.ModelSerializer):
    """Preguntas de autoevaluación con sus esquemas asociados."""

    schemas_questions = EvaluationSchemaListSerializer(many=True, read_only=True)
    class Meta:
        model = SelfEvaluationQuestions
        fields = ['id', 'description','descriptionEnglish', 'schemas_questions','evaluation_concept']

class EvaluationMetadataRegisterSerializer(serializers.Serializer):
    """Payload de alta para esquemas de metadata con validación de unicidad."""

    schema = serializers.CharField(required=True, validators=[
        UniqueValidator(queryset=EvaluationMetadata.objects.all(),
                        message="Este metadato ya esta registrado.",
                        )])
    description = serializers.CharField(required=True)
    value_importance_schema = serializers.CharField(required=True)
    code = serializers.CharField(required=True, validators=[
        UniqueValidator(queryset=EvaluationMetadata.objects.all(),
                        message="Este código ya esta registrado.",
                        )])


class EvaluationMetadataSerializer(serializers.ModelSerializer):
    """Serializer CRUD directo del modelo `EvaluationMetadata`."""

    class Meta:
        model = EvaluationMetadata
        fields = ('__all__')

class RelationshipQuestionAndMetadata(serializers.Serializer):
    """Relaciona una auto-pregunta con un esquema de metadata."""

    id_schema = serializers.IntegerField(required=True)
    id_question = serializers.IntegerField(required=True)

    class Meta:
        fields = ('id_schema','id_question')

class SchemaQualificationListSerializer(serializers.ModelSerializer):
    """Detalle de la calificación automática obtenida por esquema."""

    schema = serializers.SerializerMethodField()
    qualification = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = MetadataSchemaQualification
        fields = (
            'id',
            'qualification',
            'schema',
            'description'
        )

    @extend_schema_field(serializers.FloatField())
    def get_qualification(self, obj) -> float:
        return obj.qualification

    @extend_schema_field(serializers.CharField())
    def get_schema(self, obj) -> str:
        """Expone el texto del esquema automático evaluado."""

        query = EvaluationMetadata.objects.filter(pk=obj.evaluation_schema.id).values('schema')
        if query.exists():
            return query[0]['schema']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_description(self, obj) -> str:
        """Expone la descripción del esquema automático evaluado."""

        query = EvaluationMetadata.objects.filter(pk=obj.evaluation_schema.id).values('description')
        if query.exists():
            return query[0]['description']
        else:
            return ""


class EvaluationSerializer2(serializers.ModelSerializer):
    """Detalle automático por concepto con sus esquemas calificados."""

    evaluation_concept = EvaluationConceptSerializer(read_only=True)
    metadata_evaluations = SchemaQualificationListSerializer(read_only=True, many=True)

    class Meta:
        model = MetadataQualificationConcept
        fields = (
            'evaluation_concept',
            'average_schema',
            'metadata_evaluations',

        )


class EvaluationAutomaticEvaluationSerializer(serializers.ModelSerializer):
    """Resultado total de la evaluación automática de metadata para un OA."""

    metadata_concept_evaluations = EvaluationSerializer2(many=True, read_only=True)

    class Meta:
        model = MetadataAutomaticEvaluation
        fields = (
            'id',
            'learning_object',
            'rating_schema',
            'metadata_concept_evaluations'
        )
