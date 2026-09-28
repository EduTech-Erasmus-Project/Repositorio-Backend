"""Serializers y paginadores para metadata de objetos de aprendizaje.

Este módulo expone distintas formas de salida según el contexto:

- lectura pública de OAs
- listados resumidos para destacados y catálogos
- vistas enriquecidas con evaluaciones de estudiantes y expertos
- comentarios y acciones admin sobre el flag `public`
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.response import Response
from applications.learning_object_metadata.utils import get_rating_value
from applications.evaluation_student.serializers import EvaluationQuestionQualificationSerializer, \
    EvaluationPrinciple_QualificationsValueSerializer
from applications.evaluation_student.models import StudentEvaluation
from applications.evaluation_collaborating_expert.serializers import EvaluationConceptQualificationSerializer
from applications.license.serializers import LicenseSerializer
from applications.education_level.serializers import EducationLevelListSerializer, EducationLevelSerializer
from applications.knowledge_area.serializers import KnowledgeAreaListSerializer, KnowledgeAreaListSerializers, \
    KnowledgeAreaNameSerializer
from applications.learning_object_file.serializers import LearningObjectSerializer, LearningObjectFileSerializer
from applications.user.serializers import UserCommentSerializer, UserFullName, GeneralUserStudent_View_ListSerializer
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert
from roabackend.settings import DOMAIN
from rest_framework import serializers, pagination
from .models import Commentary, LearningObjectMetadata


class ArrayIntegerSerializer(serializers.ListField):
    """Lista tipada de enteros usada por filtros y payloads simples."""

    children = serializers.IntegerField(required=True)


class LearningObjectMetadataSerializer(serializers.ModelSerializer):
    """Serializer base de escritura para metadata sin exponer el flag `public`."""

    class Meta:
        model = LearningObjectMetadata
        exclude = ('public',)


class ROANumberPagination(pagination.PageNumberPagination):
    """Paginación estándar para listados públicos de metadata."""

    page_size = 16
    max_page_size = 50

    def get_paginated_response(self, data):
        """Devuelve la envoltura de paginación usada por el frontend."""

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
    """Paginación para resultados detallados de evaluación estudiantil."""

    page_size = 15
    max_page_size = 50

    def get_paginated_response(self, data):
        """Mantiene el shape de respuesta heredado para listados paginados."""

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
    """Paginación compacta para bloques de destacados y populares."""

    page_size = 8
    max_page_size = 50


class ROANumberPaginationObservation(pagination.PageNumberPagination):
    """Paginacion especifica para el historial propio de OAs del usuario."""

    page_size = 9
    max_page_size = 50


class LearningObjectMetadataAllSerializer(serializers.ModelSerializer):
    """Lectura completa de un OA con relaciones anidadas y banderas derivadas."""

    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    education_levels = EducationLevelSerializer(read_only=True)
    knowledge_area = KnowledgeAreaListSerializers()
    user_created = UserCommentSerializer(read_only=True)
    avatar = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    qualification_student = serializers.SerializerMethodField()
    qualification_expert = serializers.SerializerMethodField()

    class Meta:
        model = LearningObjectMetadata
        fields = ('__all__')
        extra_fields = ['rating', 'qualification_student', 'qualification_expert']

    @extend_schema_field(OpenApiTypes.INT)
    @extend_schema_field(OpenApiTypes.INT)
    @extend_schema_field(OpenApiTypes.INT)
    def get_rating(self, obj):
        """Resuelve el rating visible priorizando la evaluación experta marcada."""

        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=obj.id,
            is_priority=True
        ).values('rating')
        if not query.exists():
            query = EvaluationCollaboratingExpert.objects.filter(
                learning_object__id=obj.id,
            ).distinct('learning_object').values('rating')
        if query.exists():
            return get_rating_value(query[0]['rating'])
        else:
            return 0

    @extend_schema_field(OpenApiTypes.URI)
    @extend_schema_field(OpenApiTypes.URI)
    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar(self, obj):
        """Construye una URL absoluta para el avatar del OA."""

        if obj.avatar:
            return DOMAIN + obj.avatar.url

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_qualification_student(self, obj):
        """Indica si el OA ya tiene al menos una evaluación estudiantil."""

        query = StudentEvaluation.objects.filter(
            learning_object_id=obj.id
        )
        if query.exists():
            return True
        else:
            return False

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_qualification_expert(self, obj):
        """Indica si el OA ya fue evaluado por algún experto colaborador."""

        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object_id=obj.id
        )
        if query.exists():
            return True
        else:
            return False


class LearningObjectMetadataYears(serializers.ModelSerializer):
    """Salida mínima usada para extraer fechas de creación del OA."""

    class Meta:
        model = LearningObjectMetadata
        fields = ('created',)


class LearningObjectMetadataPopularFieldSerializer(serializers.ModelSerializer):
    """Resumen de OA para tarjetas públicas de populares y comentarios."""

    knowledge_area = KnowledgeAreaNameSerializer(read_only=True)
    user_created = UserFullName(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = LearningObjectMetadata
        fields = (
        'id', 'user_created', 'created', 'general_title', 'general_description', 'slug', 'avatar', 'knowledge_area')

    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar(self, obj):
        """Construye una URL absoluta para el avatar mostrado en listados."""

        if obj.avatar:
            return DOMAIN + obj.avatar.url


class LearningObjectMetadataPopularSerializer(serializers.ModelSerializer):
    """Representa un OA popular junto con la calificación experta visible."""

    rating = serializers.SerializerMethodField()
    learning_object = LearningObjectMetadataPopularFieldSerializer(read_only=True)

    class Meta:
        model = EvaluationCollaboratingExpert
        fields = (
            'learning_object',
            'rating'
        )

    @extend_schema_field(OpenApiTypes.INT)
    def get_rating(self, obj):
        """Normaliza el rating interno a la escala visible del frontend."""

        return get_rating_value(obj.rating)


class LearningObjectMetadataComment(serializers.ModelSerializer):
    """Salida de comentario experto asociada a un OA resumido."""

    rating = serializers.SerializerMethodField()
    learning_object = LearningObjectMetadataPopularFieldSerializer(read_only=True)

    class Meta:
        model = EvaluationCollaboratingExpert
        fields = (
            'learning_object',
            'rating',
            'observation'
        )

    @extend_schema_field(OpenApiTypes.INT)
    def get_rating(self, obj):
        """Normaliza el rating interno a la escala visible del frontend."""

        return get_rating_value(obj.rating)


class LearningObjectMetadataByExpet(serializers.ModelSerializer):
    """Detalle de evaluación experta con OA y conceptos ya expandidos.

    El nombre se mantiene por compatibilidad con el código heredado.
    """

    learning_object = LearningObjectMetadataAllSerializer(read_only=True)
    concept_evaluations = EvaluationConceptQualificationSerializer(many=True, read_only=True)
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
    """Detalle de evaluación estudiantil para un OA concreto."""

    learning_object = LearningObjectMetadataAllSerializer(read_only=True)
    studentevaluations = EvaluationQuestionQualificationSerializer(many=True, read_only=True)

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
    """Detalle de evaluación estudiantil incluyendo al estudiante autor."""

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
    """Payload mínimo para aprobar o retirar un OA del catálogo público."""

    public = serializers.BooleanField(required=True)


class LearningObjectReviewNotificationSerializer(serializers.Serializer):
    """Payload para notificar hallazgos administrativos al docente del OA."""

    message = serializers.CharField(required=True, allow_blank=False, max_length=3000)


class CommentarySerializer(serializers.ModelSerializer):
    """Serializer base para crear o editar comentarios sobre un OA."""

    class Meta:
        model = Commentary
        fields = ('__all__')


class CommentaryListSerializer(serializers.ModelSerializer):
    """Lectura de comentarios con el usuario ya expandido para listados."""

    user = UserCommentSerializer(read_only=True)

    class Meta:
        model = Commentary
        fields = [
            'user',
            'description',
            'created'
        ]


class TeacherUploadListSerializer(serializers.ModelSerializer):
    """Resumen de OAs subidos por un docente con rating y observación."""

    license = LicenseSerializer()
    learning_object_file = LearningObjectSerializer()
    knowledge_area = KnowledgeAreaListSerializer()
    avatar = serializers.SerializerMethodField()
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
            'public',
            'avatar',
            'rating',
            'slug',
            'observation',
            'is_adapted_oer'
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_rating(self, obj):
        """Devuelve la primera calificación experta visible del OA."""

        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=obj.id
        ).values('rating')
        if query.exists():
            return get_rating_value(query[0]['rating'])
        else:
            return 0

    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar(self, obj):
        """Construye una URL absoluta para el avatar del OA."""

        if obj.avatar:
            return DOMAIN + obj.avatar.url

    @extend_schema_field(OpenApiTypes.STR)
    def get_observation(self, obj):
        """Expone la observación experta principal asociada al OA."""

        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=obj.id
        ).values('observation')
        if query.exists():
            return query[0]['observation']
        else:
            return ""
