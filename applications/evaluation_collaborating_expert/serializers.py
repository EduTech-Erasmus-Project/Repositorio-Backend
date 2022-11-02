from django.db.models.base import Model
from applications.learning_object_metadata.utils import get_rating_value
from applications.user.serializers import UserCommentSerializer
from applications.knowledge_area.serializers import KnowledgeAreaListSerializer
from applications.education_level.serializers import EducationLevelListSerializer
from applications.learning_object_file.serializers import LearningObjectSerializer
from applications.license.serializers import LicenseSerializer
from roabackend.settings import CALIFICATION_OPTIONS, YES, NO, NOT_APPLY
from django.db.models.aggregates import Avg
from rest_framework.validators import UniqueValidator
from applications.learning_object_metadata.models import LearningObjectMetadata
from rest_framework import fields, serializers
from . models import (
    EvaluationConcept,
    EvaluationMetadata, 
    EvaluationQuestion,
    EvaluationQuestionsQualification,
    EvaluationConceptQualification,
    EvaluationCollaboratingExpert,
    MetadataAutomaticEvaluation,
    MetadataQualificationConcept,
    MetadataSchemaQualification
)
from applications.evaluation_collaborating_expert import models

# Serializer class
class EvaluationQuestionRegisterSerializer(serializers.Serializer):
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
    class Meta:
        model = EvaluationQuestion
        fields = ('__all__')

class EvaluationQuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationQuestion
        # nuevo datos interprete 
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
    class Meta:
        model = EvaluationConcept
        fields = ['concept',]

class EvaluationConceptListSerializer(serializers.ModelSerializer):
    questions=EvaluationQuestionListSerializer(many=True, read_only=True)
    class Meta:
        model = EvaluationConcept
        fields = ['id','concept', 'questions']

class EvaluationQuestionQualificationSerializer(serializers.ModelSerializer):
    evaluation_question= EvaluationQuestionListSerializer(read_only=True)
    qualification = serializers.SerializerMethodField()
    class Meta:
        model = EvaluationQuestionsQualification
        fields = (
            'id',
            'qualification',
            'evaluation_question'
        )
    def get_qualification(self,obj):
        if obj.qualification is not None and obj.qualification==YES:
            return CALIFICATION_OPTIONS['YES']
        elif obj.qualification is not None and obj.qualification==NO:
            return CALIFICATION_OPTIONS['NO']
        elif obj.qualification is not None and obj.qualification == NOT_APPLY:
            return CALIFICATION_OPTIONS['NOT_APPLY']
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']

class QuestionQualificationListSerializer(serializers.ModelSerializer):
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
    def get_schema(self, obj):
        query = EvaluationQuestion.objects.filter(pk = obj.evaluation_question.id).values('schema')
        if query.exists():
            return query[0]['schema']
        else:
            return ""
    def get_interpreter_yes(self, obj):
        query = EvaluationQuestion.objects.filter(pk = obj.evaluation_question.id).values('interpreter_yes')
        if query.exists():
            return query[0]['interpreter_yes']
        else:
            return ""
    def get_interpreter_no(self, obj):
        query = EvaluationQuestion.objects.filter(pk = obj.evaluation_question.id).values('interpreter_no')
        if query.exists():
            return query[0]['interpreter_no']
        else:
            return ""
    def get_interpreter_partially(self, obj):
        query = EvaluationQuestion.objects.filter(pk = obj.evaluation_question.id).values('interpreter_partially')
        if query.exists():
            return query[0]['interpreter_partially']
        else:
            return ""
    def get_interpreter_not_apply(self, obj):
        query = EvaluationQuestion.objects.filter(pk = obj.evaluation_question.id).values('interpreter_not_apply')
        if query.exists():
            return query[0]['interpreter_not_apply']
        else:
            return ""
    def get_question(self, obj):
        query = EvaluationQuestion.objects.filter(pk = obj.evaluation_question.id).values('question')
        if query.exists():
            return query[0]['question']
        else:
            return ""
    def get_question_id(self, obj):
        return obj.evaluation_question.id

    def get_qualification(self,obj):
        if obj.qualification is not None and obj.qualification==YES:
            return CALIFICATION_OPTIONS['YES']
        elif obj.qualification is not None and obj.qualification==NO:
            return CALIFICATION_OPTIONS['NO']
        elif obj.qualification is not None and obj.qualification == NOT_APPLY:
            return CALIFICATION_OPTIONS['NOT_APPLY']
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']

class LearningObjectMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningObjectMetadata
        fields = (
            'id',
            'general_title'
        )
class LearningObjectMetadataSearchSerializer(serializers.ModelSerializer):
    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    education_levels = EducationLevelListSerializer(read_only=True)
    knowledge_area = KnowledgeAreaListSerializer()
    user_created=UserCommentSerializer(read_only=True)
    class Meta:
        model = LearningObjectMetadata
        fields = ('__all__')

class EvaluationConceptQualificationSerializer(serializers.ModelSerializer):
    evaluation_concept=EvaluationConceptSerializer()
    question_evaluations=EvaluationQuestionQualificationSerializer(many=True,read_only=True)
    class Meta:
        model = EvaluationConceptQualification
        fields = (
            'id',
            'evaluation_concept',
            'question_evaluations'
        )

class EvaluationCollaboratingExpertSerializer(serializers.ModelSerializer):
    concept_evaluations=EvaluationConceptQualificationSerializer(many=True,read_only=True)
    class Meta:
        model = EvaluationCollaboratingExpert
        fields = (
            'id',
            'learning_object',
            'rating','observation',
            'concept_evaluations'
        )

class EvaluationCollaboratingExpertSearchSerializer(serializers.ModelSerializer):
    learning_object = LearningObjectMetadataSearchSerializer(read_only=True)
    class Meta:
        model = EvaluationCollaboratingExpert
        fields = ('learning_object',)

class EvaluationCollaboratingExpertAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationCollaboratingExpert
        fields = ('__all__')

class EvaluationConceptQualificationsValueSerializer(serializers.ModelSerializer):
    #print("calificado----------------------")
    evaluation_concept = EvaluationConceptSerializer()
    question_evaluations = QuestionQualificationListSerializer(many=True,read_only=True)
    average = serializers.SerializerMethodField()
    class Meta:
        model = EvaluationConceptQualification
        fields = (
            'evaluation_concept',
            'average',
            'question_evaluations',
        )
    def get_average(self, obj):
        return get_rating_value(obj.average)

class EvaluationCollaboratingExpertEvaluationSerializer(serializers.ModelSerializer):
    concept_evaluations = EvaluationConceptQualificationsValueSerializer(many=True,read_only=True)
    class Meta:
        model = EvaluationCollaboratingExpert
        fields = (
            'id',
            'observation',
            'learning_object',
            'concept_evaluations',
        )

class ArrayIntegerSerializer(serializers.ListField):
    children = serializers.IntegerField(required=True)

class ArrayStringSerializer(serializers.ListField):
    children = serializers.CharField(required=True)

class ArrayFloatSerializer(serializers.ListField):
    children = serializers.FloatField(required=True)

class ArrayDicFielSerializer(serializers.ListField):
    children = serializers.DictField(required=True)

class EvaluationExpertCreateSerializer(serializers.Serializer):
    learning_object= serializers.IntegerField(required=True)
    results= ArrayDicFielSerializer()
    observation = serializers.CharField(required=False)
    def validate(self, data):
        incident = LearningObjectMetadata.objects.filter(pk=int(data['learning_object']))
        if not incident:
            raise serializers.ValidationError(f"Not exist oa with code {int(data['learning_object'])}")
        for value in data['results']:
            if len(EvaluationQuestion.objects.filter(pk=value['id']))==0:
                 raise serializers.ValidationError(f"Not exist question with pk {value['id']}")
        for option in data['results']:
            if option['value'] != CALIFICATION_OPTIONS['YES'] and option['value'] != CALIFICATION_OPTIONS['NO'] and option['value'] != CALIFICATION_OPTIONS['PARTIALLY'] and option['value'] != CALIFICATION_OPTIONS['NOT_APPLY']:
                raise serializers.ValidationError(f"Options are Si, No, Parcialmente and No aplica")
        return data

class LearningObjectMetadataSearchSerializer(serializers.ModelSerializer):
    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    education_levels = EducationLevelListSerializer(read_only=True)
    knowledge_area = KnowledgeAreaListSerializer()
    user_created=UserCommentSerializer(read_only=True)
    class Meta:
        model = LearningObjectMetadata
        fields = ('__all__')

class EvaluationCollaboratingExpertSearchSerializer(serializers.ModelSerializer):
    learning_object = LearningObjectMetadataSearchSerializer(read_only=True)
    class Meta:
        model = EvaluationCollaboratingExpert
        fields = ('learning_object',)

class EvaluationConceptSearchSerializer(serializers.ModelSerializer):
    evaluation_collaborating_expert = EvaluationCollaboratingExpertSearchSerializer(read_only=True)
    class Meta:
        model = EvaluationConceptQualification
        fields = (
            'evaluation_collaborating_expert',
        )
class QuestionQualificationSearchSerializer(serializers.ModelSerializer):
    concept_evaluations = EvaluationConceptSearchSerializer(read_only=True)
    class Meta:
        model = EvaluationQuestionsQualification
        fields = ('concept_evaluations',)


###################-Nuevos Serializers-##############

class EvaluationSchemaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationMetadata
        fields = ('id','schema','description','value_importance_schema','code')

class EvaluationConceptListSerializerSCHEMA(serializers.ModelSerializer):
    schemas=EvaluationSchemaListSerializer(many=True, read_only=True)
    class Meta:
        model = EvaluationConcept
        fields = ['id','concept', 'schemas']

#
class EvaluationMetadataRegisterSerializer(serializers.Serializer):
    schema = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=EvaluationMetadata.objects.all(), 
        message="Este metadato ya esta registrado.",
        )])
    description = serializers.CharField(required=True)
    value_importance_schema=serializers.CharField(required=True)
    code = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=EvaluationMetadata.objects.all(), 
        message="Este código ya esta registrado.",
        )])

class EvaluationMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationMetadata
        fields = ('__all__')

###########Nuevos Serializables para consulta de automatico

class SchemaQualificationListSerializer(serializers.ModelSerializer):
    schema = serializers.SerializerMethodField()
    qualification = serializers.SerializerMethodField()
    description=serializers.SerializerMethodField()
    class Meta:
        model = MetadataSchemaQualification
        fields = (
            'id',
            'qualification',
            'schema',
            'description'
        )
    def get_qualification(self,obj):
        return obj.qualification
    def get_schema(self, obj):
        query = EvaluationMetadata.objects.filter(pk = obj.evaluation_schema.id).values('schema')
        if query.exists():
            return query[0]['schema']
        else:
            return ""
    def get_description(self, obj):
        query = EvaluationMetadata.objects.filter(pk = obj.evaluation_schema.id).values('description')
        if query.exists():
            return query[0]['description']
        else:
            return ""
     
class EvaluationSerializer2(serializers.ModelSerializer):
    
    evaluation_concept=EvaluationConceptSerializer(read_only=True)
    metadata_evaluations = SchemaQualificationListSerializer(read_only=True,many=True)
    #print("asaaaaaaaaaaaaaaaaaaaaaaaaa",metadata_evaluations)
    class Meta:
        model = MetadataQualificationConcept
        fields = (
            'evaluation_concept',
            'average_schema',
            'metadata_evaluations',
          
        )
  
class EvaluationAutomaticEvaluationSerializer(serializers.ModelSerializer):
    metadata_concept_evaluations =EvaluationSerializer2(many=True,read_only=True)
    class Meta:
        model = MetadataAutomaticEvaluation
        fields = (
            'id',
            'learning_object',
            'rating_schema' ,
            'metadata_concept_evaluations'
        )