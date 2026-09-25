"""Serializers para la evaluación estudiantil de objetos de aprendizaje.

El archivo mezcla cuatro grupos principales:

- serialización de la rúbrica que consume el frontend
- validación de payloads para crear evaluaciones estudiantiles
- serializers de consulta con resultados agregados
- serializers CRUD para principios, lineamientos y preguntas
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework.validators import UniqueValidator
from roabackend.settings import CALIFICATION_OPTIONS, YES,NO, NOT_APPLY
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.evaluation_student.models import EvaluationGuidelineQualification, EvaluationPrincipleQualification, EvaluationQuestionQualification, Guideline, Principle, Question, StudentEvaluation
from rest_framework import serializers
class StudentQuestionSerializer(serializers.ModelSerializer):
    """Expone una pregunta de la rúbrica con sus intérpretes de respuesta."""

    class Meta:
        model = Question
        fields = (
            'id',
            'question',
            'description',
            'metadata',
            'interpreter_st_yes',
            'interpreter_st_no',
            'interpreter_st_partially',
            'interpreter_st_not_apply',
            'value_st_importance'
            )

class GuidelineSerializer(serializers.ModelSerializer):
    """Entrega un lineamiento junto con sus preguntas ordenadas."""

    questions = serializers.SerializerMethodField()
    class Meta:
        model = Guideline
        fields = (
            'id',
            'guideline', 
            'questions'
            )

    @extend_schema_field(StudentQuestionSerializer(many=True))
    def get_questions(self, obj) -> list:
        """Resuelve las preguntas hijas del lineamiento en el orden histórico del módulo."""
        queryset = obj.questions.all().order_by('id')
        return StudentQuestionSerializer(queryset, many=True).data

class PrincipleSerializer(serializers.ModelSerializer):
    """Entrega un principio con toda su jerarquía de lineamientos y preguntas."""

    guidelines = serializers.SerializerMethodField()
    class Meta:
        model = Principle
        fields = (
            'id',
            'principle',
            'guidelines',
            )

    @extend_schema_field(GuidelineSerializer(many=True))
    def get_guidelines(self, obj) -> list:
        """Resuelve los lineamientos hijos del principio en orden estable."""
        queryset = obj.guidelines.all().order_by('id')
        return GuidelineSerializer(queryset, many=True).data

class EvaluationQuestionQualificationSerializer(serializers.ModelSerializer):
    """Representa la calificación persistida para una pregunta respondida."""

    evaluation_question = StudentQuestionSerializer(required=True)
    class Meta:
        model = EvaluationQuestionQualification
        fields = (
            'id',
            'evaluation_question',
            'qualification'
            )

class LearningObjectMetadataSerialize(serializers.ModelSerializer):
    """Versión resumida del OA para respuestas de evaluación estudiantil."""

    class Meta:
        model= LearningObjectMetadata
        exclude = ('public', )

class StudentEvaluationSerializer(serializers.ModelSerializer):
    """Serializa una evaluación estudiantil con el OA y sus respuestas base."""

    learning_object= LearningObjectMetadataSerialize(read_only=True)
    studentevaluations = EvaluationQuestionQualificationSerializer(many=True,read_only=True)
    class Meta:
        model = StudentEvaluation
        fields = (
            'id',
            'rating',
            'observation',
            'learning_object',
            'studentevaluations',
            'student'
            )

class ArrayIntegerSerializer(serializers.ListField):
    """Helper legacy para listas de enteros en requests simples."""
    children = serializers.IntegerField(required=True)

class ArrayFloatSerializer(serializers.ListField):
    """Helper legacy para listas de flotantes en requests simples."""
    children = serializers.FloatField(required=True)

class ArrayDicFielSerializer(serializers.ListField):
    """Lista de diccionarios usada para enviar respuestas por pregunta."""
    children = serializers.DictField(required=True)

class EvaluationStudentCreateSerializer(serializers.Serializer):
    """Valida la carga que crea o actualiza una evaluación estudiantil."""

    learning_object= serializers.IntegerField(required=True)
    results= ArrayDicFielSerializer()
    observation = serializers.CharField(required=False)

    def validate(self, data):
        """Verifica existencia del OA, preguntas y opciones permitidas."""
        incident = LearningObjectMetadata.objects.filter(pk=int(data['learning_object']))
        if not incident:
            raise serializers.ValidationError(f"Not exist oa with code {int(data['learning_object'])}")
        for value in data['results']:
            if not Question.objects.filter(pk=value['id']).exists():
                 raise serializers.ValidationError(f"Not exist question with pk {value['id']}")
        for option in data['results']:
            if option['value'] != CALIFICATION_OPTIONS['YES'] and option['value'] != CALIFICATION_OPTIONS['NO'] and option['value'] != CALIFICATION_OPTIONS['PARTIALLY'] and option['value'] != CALIFICATION_OPTIONS['NOT_APPLY']:
                raise serializers.ValidationError(f"Options are Si, No, No aplica and Parcialmente")
        return data

class EvaluationQuestionStSerializer(serializers.ModelSerializer):
    """Serializer CRUD directo para preguntas de la rúbrica estudiantil."""

    class Meta:
        model = Question
        fields = ('__all__')

class EvaluationQuestionStRegisterSerializer(serializers.Serializer):
    """Valida el alta o actualización manual de preguntas estudiantiles."""

    """question = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=Question.objects.all(), 
        message="Esta pregunta ya esta registrado.",
        )])"""
    question = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    metadata = serializers.CharField(required=True)
    ###################################################
    interpreter_st_yes = serializers.CharField(required=True)
    interpreter_st_no = serializers.CharField(required=True)
    interpreter_st_partially = serializers.CharField(required=True)
    interpreter_st_not_apply = serializers.CharField(required=True)
    value_st_importance = serializers.CharField(required=True)

    weight = serializers.CharField(required=True)
    relevance = serializers.CharField(required=True)
    ###################################################

class EvaluationPrincipleSerializer(serializers.ModelSerializer):
    """Salida reducida de un principio para listados simples."""

    class Meta:
        model = Principle
        fields = ['principle',] 

class EvaluationSchemaListSerializer(serializers.ModelSerializer):
    """Expone la configuración completa de una pregunta dentro del schema."""

    class Meta:
        model = Question
        fields = ('id',
        'question',
        'metadata',
        'description',
        'interpreter_st_yes',
        'interpreter_st_no',
        'interpreter_st_partially',
        'interpreter_st_not_apply',
        'value_st_importance',
        'weight',
        'relevance'
        )

class EvaluationGuidelinesListSerializer(serializers.ModelSerializer):
    """Entrega un lineamiento con todas sus preguntas de schema."""

    questions=EvaluationSchemaListSerializer(many=True, read_only=True)
    class Meta:
        model = Guideline
        fields = ['id','guideline', 'questions']

class EvaluationPrincipleListSerializer(serializers.ModelSerializer):
    """Entrega un principio con su estructura completa para administración."""

    guidelines=EvaluationGuidelinesListSerializer(many=True, read_only=True)
    class Meta:
        model = Principle
        fields = ['id','principle', 'guidelines']

class EvaluationQuestionListStudentSerializer(serializers.ModelSerializer):
    """Pregunta presentada al reconstruir una evaluación ya respondida."""

    class Meta:
        model = Question
        fields = (
            'id',
            'question',
            'description',
            'metadata',
            'interpreter_st_yes',
            'interpreter_st_no',
            'interpreter_st_partially',
            'interpreter_st_not_apply',
            'value_st_importance')

class EvaluationQuestionEstudentQualificationSerializer(serializers.ModelSerializer):
    """Convierte la calificación númerica guardada a la opción textual del frontend."""

    evaluation_question= EvaluationQuestionListStudentSerializer(read_only=True)
    qualification = serializers.SerializerMethodField()
    class Meta:
        model = EvaluationQuestionQualification
        fields = (
            'id',
            'qualification',
            'evaluation_question'
        )
    @extend_schema_field(serializers.CharField())
    def get_qualification(self,obj) -> str:
        """Mapea el valor persistido a la etiqueta de opción histórica."""
        if obj.qualification is not None and float(YES) == float(obj.qualification):
            return CALIFICATION_OPTIONS['YES']
        elif obj.qualification is not None and float(NO) == float(obj.qualification):
            return CALIFICATION_OPTIONS['NO']
        elif obj.qualification is not None and float(obj.qualification) == float(NOT_APPLY):
            return CALIFICATION_OPTIONS['NOT_APPLY']
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']


class Evaluation_StudentGuidelineQualificationSerializer(serializers.ModelSerializer):
    """Agrupa preguntas respondidas bajo un lineamiento evaluado."""

    guideline=GuidelineSerializer()
    questions_student_evaluations=EvaluationQuestionEstudentQualificationSerializer(many=True,read_only=True)
    class Meta:
        model = EvaluationGuidelineQualification
        fields = (
            'id',
            'guideline',
            'questions_student_evaluations'
        )

class Evaluation_StudentPrincipleQualificationSerializer(serializers.ModelSerializer):
    """Agrupa lineamientos evaluados bajo un principio respondido."""

    principle=PrincipleSerializer()
    guideline_evaluations=Evaluation_StudentGuidelineQualificationSerializer(many=True,read_only=True)
    class Meta:
        model = EvaluationPrincipleQualification
        fields = (
            'id',
            'principle',
            'guideline_evaluations'
        )


class Evaluation_Student_Serializer(serializers.ModelSerializer):
    """Salida jerárquica de una evaluación estudiantil completa."""

    principle_evaluations=Evaluation_StudentPrincipleQualificationSerializer(many=True,read_only=True)
    class Meta:
        model = StudentEvaluation
        fields = (
            'id',
            'learning_object',
            'rating',
            'observation',
            'principle_evaluations',
        )
    
class QuestionSerializer(serializers.ModelSerializer):
    """Expone cada respuesta con texto, metadata e intérpretes asociados."""

    question = serializers.SerializerMethodField()
    question_id = serializers.SerializerMethodField()
    qualification = serializers.SerializerMethodField()
    interpreter_st_yes = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    interpreter_st_no = serializers.SerializerMethodField()
    interpreter_st_partially = serializers.SerializerMethodField()
    interpreter_st_not_apply = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationQuestionQualification
        fields = (
            'id',
            'question_id',
            'question',
            'metadata',
            'qualification',
            'interpreter_st_yes',
            'interpreter_st_no',
            'interpreter_st_partially',
            'interpreter_st_not_apply',
        )
    @extend_schema_field(serializers.CharField())
    def get_interpreter_st_no(self, obj) -> str:
        """Obtiene el texto asociado a la opción negativa de la pregunta."""
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('interpreter_st_no')
        if query.exists():
            return query[0]['interpreter_st_no']
        else:
            return ""
    @extend_schema_field(serializers.CharField())
    def get_interpreter_st_partially(self, obj) -> str:
        """Obtiene el texto asociado a la opción parcial de la pregunta."""
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('interpreter_st_partially')
        if query.exists():
            return query[0]['interpreter_st_partially']
        else:
            return ""
    @extend_schema_field(serializers.CharField())
    def get_metadata(self, obj) -> str:
        """Obtiene la metadata textual asociada a la pregunta evaluada."""
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('metadata')
        if query.exists():
            return query[0]['metadata']
        else:
            return ""
    @extend_schema_field(serializers.CharField())
    def get_interpreter_st_yes(self, obj) -> str:
        """Obtiene el texto asociado a la opción afirmativa de la pregunta."""
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('interpreter_st_yes')
        if query.exists():
            return query[0]['interpreter_st_yes']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_interpreter_st_not_apply(self, obj) -> str:
        """Obtiene el texto asociado a la opción de no aplica."""
        query = Question.objects.filter(pk=obj.evaluation_question.id).values('interpreter_st_not_apply')
        if query.exists():
            return query[0]['interpreter_st_not_apply']
        else:
            return ""

    @extend_schema_field(serializers.CharField())
    def get_question(self, obj) -> str:
        """Recupera el texto visible de la pregunta evaluada."""
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('question')
        if query.exists():
            return query[0]['question']
        else:
            return ""
    @extend_schema_field(serializers.IntegerField())
    def get_question_id(self, obj) -> int:
        """Devuelve el identificador de la pregunta original."""
        return obj.evaluation_question.id

    @extend_schema_field(serializers.CharField())
    def get_qualification(self,obj) -> str:
        """Convierte la nota numérica al valor textual esperado por el frontend."""
        if obj.qualification is not None and float(YES) == float(obj.qualification):
            return CALIFICATION_OPTIONS['YES']
        elif obj.qualification is not None and float(NO) == float(obj.qualification):
            return CALIFICATION_OPTIONS['NO']
        elif obj.qualification is not None and float(obj.qualification) == float(NOT_APPLY):
            return CALIFICATION_OPTIONS['NOT_APPLY']
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']

class EvaluationGuidelineSTSerializer(serializers.ModelSerializer):
    """Salida reducida de un lineamiento para resultados agregados."""

    class Meta:
        model = Guideline
        fields = ['guideline']
    

class EvaluationGuideline_QualificationsValueSerializer(serializers.ModelSerializer):
    """Expone promedio de lineamiento junto con sus respuestas por pregunta."""

    guideline_pr=EvaluationGuidelineSTSerializer(read_only=True)
    guideline_evaluations=serializers.SerializerMethodField()
    class Meta:
        model = EvaluationGuidelineQualification
        fields = (
            'id',
            'average_guideline',
            'guideline_pr',
            'guideline_evaluations'
            
        )

    @extend_schema_field(QuestionSerializer(many=True))
    def get_guideline_evaluations(self, obj) -> list:
        """Ordena y serializa las respuestas asociadas al lineamiento evaluado."""
        queryset = obj.guideline_evaluations.all().order_by('evaluation_question__id')
        return QuestionSerializer(queryset, many=True).data

class EvaluationPrincipleSTSerializer(serializers.ModelSerializer):
    """Salida reducida de un principio para resultados agregados."""

    class Meta:
        model = Principle
        fields = ['principle']
    

class EvaluationPrinciple_QualificationsValueSerializer(serializers.ModelSerializer):
    """Expone promedio de principio junto con sus lineamientos evaluados."""

    evaluation_principle=EvaluationPrincipleSTSerializer(read_only=True)
    principle_gl=serializers.SerializerMethodField()
    class Meta:
        model = EvaluationPrincipleQualification
        fields = (
            'id',
            'average_principle',
            'evaluation_principle',
            'principle_gl'

        )

    @extend_schema_field(EvaluationGuideline_QualificationsValueSerializer(many=True))
    def get_principle_gl(self, obj) -> list:
        """Ordena y serializa los lineamientos asociados al principio evaluado."""
        queryset = obj.principle_gl.all().order_by('guideline_pr__id')
        return EvaluationGuideline_QualificationsValueSerializer(queryset, many=True).data


class EvaluationStudentList_EvaluationSerializer(serializers.ModelSerializer):
    """Salida detallada de una evaluación con todos sus agregados jerárquicos."""

    evaluation_students= serializers.SerializerMethodField()
    class Meta:
        model = StudentEvaluation
        fields = (
            'id', 
            'learning_object',
            'rating',
            'observation',
            'evaluation_students'
        )

    @extend_schema_field(EvaluationPrinciple_QualificationsValueSerializer(many=True))
    def get_evaluation_students(self, obj) -> list:
        """Serializa los promedios por principio en orden estable."""
        queryset = obj.evaluation_students.all().order_by('evaluation_principle__id')
        return EvaluationPrinciple_QualificationsValueSerializer(queryset, many=True).data

class EvaluationPrincipleRegSerializer(serializers.ModelSerializer):
    """Serializer CRUD minimo para principios de la rúbrica."""

    class Meta:
        model = Principle
        fields = ['principle',]

class EvaluationPrincipleGuidelineRegSchemaListSerializer(serializers.ModelSerializer):
    """Pregunta incluida al listar la estructura completa de un principio."""

    class Meta:
        model = Question
        fields = ('id','question','metadata'
        ,'description',
        'interpreter_st_yes',
        'interpreter_st_no',
        'interpreter_st_partially',
        'interpreter_st_not_apply',
        'value_st_importance',
        'weight',
        'relevance'
        )

class EvaluationPrincipleGuidelineRegListSerializer(serializers.ModelSerializer):
    """Lineamiento incluido al listar la estructura completa de un principio."""

    questions=EvaluationPrincipleGuidelineRegSchemaListSerializer(many=True, read_only=True)
    class Meta:
        model = Guideline
        fields = ['id','guideline', 'questions']

class EvaluationPrincipleRegListSerializer(serializers.ModelSerializer):
    """Principio con sus lineamientos y preguntas para vistas administrativas."""

    guidelines=EvaluationPrincipleGuidelineRegListSerializer(many=True, read_only=True)
    class Meta:
        model = Principle
        fields = ['id','principle','guidelines']

class EvaluationQuestionGuidelinesRegSerializer(serializers.ModelSerializer):
    """Serializer CRUD directo para lineamientos."""

    class Meta:
        model = Guideline
        fields = ('__all__')

class EvaluationGuidelineValidRegisterSerializer(serializers.Serializer):
    """Valida el registro de lineamientos con restricción de unicidad."""

    guideline = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=Guideline.objects.all(), 
        message="Esta ya esta registrado.",
        )])
