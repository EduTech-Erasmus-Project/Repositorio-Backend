from rest_framework.response import Response
from applications.learning_object_metadata.utils import get_rating_value
from applications.evaluation_student.serializers import EvaluationQuestionQualificationSerializer,EvaluationPrinciple_QualificationsValueSerializer
from applications.evaluation_student.models import StudentEvaluation
from applications.evaluation_collaborating_expert.serializers import EvaluationConceptQualificationSerializer
from applications.license.serializers import LicenseSerializer
from applications.education_level.serializers import EducationLevelListSerializer, EducationLevelSerializer
from applications.knowledge_area.serializers import KnowledgeAreaListSerializer, KnowledgeAreaListSerializers, KnowledgeAreaNameSerializer
from applications.learning_object_file.serializers import LearningObjectSerializer
from applications.user.serializers import UserCommentSerializer, UserFullName, GeneralUserStudent_View_ListSerializer
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert
from roabackend.settings import DOMAIN
from rest_framework import serializers,pagination
from .models import Commentary, LearningObjectMetadata

class ArrayIntegerSerializer(serializers.ListField):
    children = serializers.IntegerField(required=True)

class LearningObjectMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model= LearningObjectMetadata
        exclude = ('public', )

class ROANumberPagination(pagination.PageNumberPagination):
    page_size = 15
    max_page_size = 50
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'links': {
               'next': self.get_next_link(),
               'previous': self.get_previous_link()
            },
            'pages': self.page.paginator.num_pages,
            'results': data
        })

class ROANumberPagination_Estudent_Qualification(pagination.PageNumberPagination):
    page_size = 15
    max_page_size = 50
    def get_paginated_response(self, data):

        #data['results'].average =

        return Response({
            'count': self.page.paginator.count,
            'links': {
               'next': self.get_next_link(),
               'previous': self.get_previous_link()
            },
            'pages': self.page.paginator.num_pages,
            'results': data
        })
class ROANumberPaginationPopular(pagination.PageNumberPagination):
    page_size = 8
    max_page_size = 50

class LearningObjectMetadataAllSerializer(serializers.ModelSerializer):
    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    education_levels = EducationLevelSerializer(read_only=True)
    knowledge_area = KnowledgeAreaListSerializers()
    user_created=UserCommentSerializer(read_only=True)
    rating = serializers.SerializerMethodField()
    qualification_student = serializers.SerializerMethodField()
    qualification_expert = serializers.SerializerMethodField()
    class Meta:
        model = LearningObjectMetadata
        fields = ('__all__')
        extra_fields = ['rating','qualification_student','qualification_expert']

    def get_rating(self, obj):
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=obj.id,
            is_priority=True
        ).values('rating')
        if len(query) == 0:
            query = EvaluationCollaboratingExpert.objects.filter(
                learning_object__id=obj.id,
            ).distinct('learning_object').values('rating')
        if query.exists():
            return get_rating_value(query[0]['rating'])
        else:
            return 0

    def get_qualification_student(self,obj):
        query = StudentEvaluation.objects.filter(
            learning_object_id=obj.id
        )
        if query.exists():
            return True
        else:
            return False
    def get_qualification_expert(self,obj):
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object_id=obj.id
        )
        if query.exists():
            return True
        else:
            return False


class LearningObjectMetadataYears(serializers.ModelSerializer):
    class Meta:
        model = LearningObjectMetadata
        fields = ('created',)

class LearningObjectMetadataPopularFieldSerializer(serializers.ModelSerializer):
    knowledge_area = KnowledgeAreaNameSerializer(read_only=True)
    user_created= UserFullName(read_only=True)
    class Meta:
        model= LearningObjectMetadata
        fields = ('id','user_created','created','general_title','general_description','slug','avatar','knowledge_area')


class LearningObjectMetadataPopularSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    learning_object= LearningObjectMetadataPopularFieldSerializer(read_only=True)
    class Meta:
        model= EvaluationCollaboratingExpert
        fields = (
            'learning_object',
            'rating'
            )
    def get_rating(self, obj):
        data = get_rating_value(obj.rating)
        return data

class LearningObjectMetadataComment(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    learning_object= LearningObjectMetadataPopularFieldSerializer(read_only=True)
    class Meta:
        model= EvaluationCollaboratingExpert
        fields = (
            'learning_object',
            'rating',
            'observation'
            )
    def get_rating(self, obj):
        data = get_rating_value(obj.rating)
        return data

class LearningObjectMetadataByExpet(serializers.ModelSerializer):
    learning_object = LearningObjectMetadataAllSerializer(read_only=True)
    concept_evaluations = EvaluationConceptQualificationSerializer(many=True,read_only=True)
    collaborating_expert = GeneralUserStudent_View_ListSerializer(read_only=True)
    class Meta:
        model = EvaluationCollaboratingExpert
        fields = (
            'id',
            'rating',
            'observation',
            'learning_object',
            'is_priority',
            'concept_evaluations',
            'collaborating_expert'
            )

class LearningObjectMetadataByStudent(serializers.ModelSerializer):
    learning_object = LearningObjectMetadataAllSerializer(read_only=True)
    studentevaluations = EvaluationQuestionQualificationSerializer(many=True,read_only=True)

    class Meta:
        model = StudentEvaluation
        fields = (
            'id',
            'observation',
            'rating',
            'learning_object',
            'studentevaluations',
            )


class LearningObjectMetadataByStudentQualification(serializers.ModelSerializer):
    learning_object = LearningObjectMetadataAllSerializer(read_only=True)
    studentevaluations = EvaluationQuestionQualificationSerializer(many=True, read_only=True)
    student = GeneralUserStudent_View_ListSerializer(read_only=True)
    class Meta:
        model = StudentEvaluation
        fields = (
            'id',
            'observation',
            'rating',
            'learning_object',
            'student',
            'studentevaluations'
        )

class AdminLearningObjectMetadataPublicUpdateSerializer(serializers.Serializer):
    public = serializers.BooleanField(required=True)

# Commentary
class CommentarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentary
        fields = ('__all__')
        
class CommentaryListSerializer(serializers.ModelSerializer):
    user = UserCommentSerializer(read_only=True)
    class Meta:
        model = Commentary
        fields = [
            'user',
            'description', 
            'created'
            ]

class TeacherUploadListSerializer(serializers.ModelSerializer):
    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    knowledge_area = KnowledgeAreaListSerializer()
    rating = serializers.SerializerMethodField()
    observation = serializers.SerializerMethodField()
    class Meta:
        model = LearningObjectMetadata
        fields = [
            'id',
            'license', 
            'learning_object_file',
            'knowledge_area',
            'general_title',
            'general_description', 
            'avatar', 
            'rating',
            'slug',
            'observation',
            'is_adapted_oer'
            ]
    def get_rating(self, obj):
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=obj.id
        ).values('rating')
        if query.exists():
            return get_rating_value(query[0]['rating'])
        else:
            return 0
    def get_observation(self, obj):
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=obj.id
        ).values('observation')
        if query.exists():
            return query[0]['observation']
        else:
            return ""
