from rest_framework.validators import UniqueValidator
from roabackend.settings import CALIFICATION_OPTIONS, YES,NO
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.evaluation_student.models import EvaluationGuidelineQualification, EvaluationPrincipleQualification, EvaluationQuestionQualification, Guideline, Principle, Question, StudentEvaluation
from rest_framework import serializers
# Serializers

class StudentQuestionSerializer(serializers.ModelSerializer):
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
            'value_st_importance'
            )

class GuidelineSerializer(serializers.ModelSerializer):
    questions = StudentQuestionSerializer(many=True)
    class Meta:
        model = Guideline
        fields = (
            'id',
            'guideline', 
            'questions'
            )
class PrincipleSerializer(serializers.ModelSerializer):
    guidelines = GuidelineSerializer(many=True)
    class Meta:
        model = Principle
        fields = (
            'id',
            'principle',
            'guidelines',
            )

class EvaluationQuestionQualificationSerializer(serializers.ModelSerializer):
    evaluation_question = StudentQuestionSerializer(required=True)
    class Meta:
        model = EvaluationQuestionQualification
        fields = (
            'id',
            'evaluation_question',
            'qualification'
            )

class LearningObjectMetadataSerialize(serializers.ModelSerializer):
    class Meta:
        model= LearningObjectMetadata
        exclude = ('public', )

class StudentEvaluationSerializer(serializers.ModelSerializer):
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
    children = serializers.IntegerField(required=True)

class ArrayFloatSerializer(serializers.ListField):
    children = serializers.FloatField(required=True)
########################################################serializer para enviar las respuestas#######################################################

class ArrayDicFielSerializer(serializers.ListField):
    children = serializers.DictField(required=True)

class EvaluationStudentCreateSerializer(serializers.Serializer):
    learning_object= serializers.IntegerField(required=True)
    results= ArrayDicFielSerializer()
    observation = serializers.CharField(required=False)
    def validate(self, data):
        incident = LearningObjectMetadata.objects.filter(pk=int(data['learning_object']))
        if not incident:
            raise serializers.ValidationError(f"Not exist oa with code {int(data['learning_object'])}")
        for value in data['results']:
            if len(Question.objects.filter(pk=value['id']))==0:
                 raise serializers.ValidationError(f"Not exist question with pk {value['id']}")
        for option in data['results']:
            if option['value'] != CALIFICATION_OPTIONS['YES'] and option['value'] != CALIFICATION_OPTIONS['NO'] and option['value'] != CALIFICATION_OPTIONS['PARTIALLY']:
                raise serializers.ValidationError(f"Options are Si, No and Parcialmente")
        return data

#############################CRUD PREGUNTAS

class EvaluationQuestionStSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('__all__')

class EvaluationQuestionStRegisterSerializer(serializers.Serializer):
    question = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=Question.objects.all(), 
        message="Esta pregunta ya esta registrado.",
        )])
    description = serializers.CharField(required=True)
    metadata = serializers.CharField(required=True)
    ###################################################
    interpreter_st_yes = serializers.CharField(required=True)
    interpreter_st_no = serializers.CharField(required=True)
    interpreter_st_partially = serializers.CharField(required=True)
    value_st_importance = serializers.CharField(required=True)
    ###################################################

###list

class EvaluationPrincipleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Principle
        fields = ['principle',] 

class EvaluationSchemaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id','question','metadata'
        ,'description',
        'interpreter_st_yes',
        'interpreter_st_no',
        'interpreter_st_partially',
        'interpreter_st_partially',
        'value_st_importance'
        )

class EvaluationGuidelinesListSerializer(serializers.ModelSerializer):
    questions=EvaluationSchemaListSerializer(many=True, read_only=True)
    class Meta:
        model = Guideline
        fields = ['id','guideline', 'questions']

class EvaluationPrincipleListSerializer(serializers.ModelSerializer):
    guidelines=EvaluationGuidelinesListSerializer(many=True, read_only=True)
    class Meta:
        model = Principle
        fields = ['id','principle', 'guidelines']


#####################serializers del create evaluation

class EvaluationQuestionListStudentSerializer(serializers.ModelSerializer):
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
            'value_st_importance')

class EvaluationQuestionEstudentQualificationSerializer(serializers.ModelSerializer):
    evaluation_question= EvaluationQuestionListStudentSerializer(read_only=True)
    qualification = serializers.SerializerMethodField()
    class Meta:
        model = EvaluationQuestionQualification
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
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']


class Evaluation_StudentGuidelineQualificationSerializer(serializers.ModelSerializer):
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
    
##########################de consulta de la evaluacion
class QuestionSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    question_id = serializers.SerializerMethodField()
    qualification = serializers.SerializerMethodField()
    interpreter_st_yes = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    interpreter_st_no = serializers.SerializerMethodField()
    interpreter_st_partially = serializers.SerializerMethodField()
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
        )
    def get_interpreter_st_no(self, obj):
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('interpreter_st_no')
        if query.exists():
            return query[0]['interpreter_st_no']
        else:
            return ""
    def get_interpreter_st_partially(self, obj):
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('interpreter_st_partially')
        if query.exists():
            return query[0]['interpreter_st_partially']
        else:
            return ""
    def get_metadata(self, obj):
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('metadata')
        if query.exists():
            return query[0]['metadata']
        else:
            return ""
    def get_interpreter_st_yes(self, obj):
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('interpreter_st_yes')
        if query.exists():
            return query[0]['interpreter_st_yes']
        else:
            return ""
    def get_question(self, obj):
        query = Question.objects.filter(pk = obj.evaluation_question.id).values('question')
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
        else:
            return CALIFICATION_OPTIONS['PARTIALLY']





class EvaluationGuidelineSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guideline
        fields = ['guideline']
    

class EvaluationGuideline_QualificationsValueSerializer(serializers.ModelSerializer):
    guideline_pr=EvaluationGuidelineSTSerializer(read_only=True)
    guideline_evaluations=QuestionSerializer(many=True,read_only=True)
    class Meta:
        model = EvaluationGuidelineQualification
        fields = (
            'id',
            'average_guideline',
            'guideline_pr',
            'guideline_evaluations'
            
        )

class EvaluationPrincipleSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Principle
        fields = ['principle']
    

class EvaluationPrinciple_QualificationsValueSerializer(serializers.ModelSerializer):
    evaluation_principle=EvaluationPrincipleSTSerializer(read_only=True)
    principle_gl=EvaluationGuideline_QualificationsValueSerializer(many=True,read_only=True)
    class Meta:
        model = EvaluationPrincipleQualification
        fields = (
            'id',
            'average_principle',
            'evaluation_principle',
            'principle_gl'

        )


class EvaluationStudentList_EvaluationSerializer(serializers.ModelSerializer):
    evaluation_students= EvaluationPrinciple_QualificationsValueSerializer(many=True,read_only=True)
    class Meta:
        model = StudentEvaluation
        fields = (
            'id', 
            'learning_object',
            'rating',
            'observation',
            'evaluation_students'
        )

####################serializers del crud de principios

class EvaluationPrincipleRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Principle
        fields = ['principle',]

class EvaluationPrincipleGuidelineRegSchemaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id','question','metadata'
        ,'description',
        'interpreter_st_yes',
        'interpreter_st_no',
        'interpreter_st_partially',
        'interpreter_st_partially',
        'value_st_importance'
        )

class EvaluationPrincipleGuidelineRegListSerializer(serializers.ModelSerializer):
    questions=EvaluationPrincipleGuidelineRegSchemaListSerializer(many=True, read_only=True)
    class Meta:
        model = Guideline
        fields = ['id','guideline', 'questions']

class EvaluationPrincipleRegListSerializer(serializers.ModelSerializer):
    guidelines=EvaluationPrincipleGuidelineRegListSerializer(many=True, read_only=True)
    class Meta:
        model = Principle
        fields = ['id','principle','guidelines']

##################CRUD DE GUIDELINES

class EvaluationQuestionGuidelinesRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guideline
        fields = ('__all__')

class EvaluationGuidelineValidRegisterSerializer(serializers.Serializer):
    guideline = serializers.CharField(required=True,validators=[
        UniqueValidator(queryset=Guideline.objects.all(), 
        message="Esta ya esta registrado.",
        )])