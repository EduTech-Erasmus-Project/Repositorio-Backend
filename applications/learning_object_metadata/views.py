"""Vistas y filtros para explorar, publicar y evaluar metadata de OAs.

Este módulo mezcla tres responsabilidades históricas del proyecto:

- exponer catálogos y búsquedas públicas de objetos de aprendizaje
- administrar aprobación, comentarios y listados para paneles internos
- disparar la evaluación autómatica o manual de metadata tras la carga del OA
"""

import django_filters
from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from applications.interaction.models import Interaction
from applications.evaluation_collaborating_expert.serializers import QuestionQualificationSearchSerializer, \
    EvaluationCollaboratingExpertEvaluationSerializer, EvaluationCollaboratingExpertAllSerializer, SelfEvaluationQuestions
from applications.evaluation_student.models import StudentEvaluation
from applications.evaluation_student.serializers import EvaluationStudentList_EvaluationSerializer
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert, EvaluationConcept, \
    EvaluationMetadata, EvaluationQuestionsQualification, MetadataAutomaticEvaluation, MetadataQualificationConcept, \
    MetadataSchemaQualification, MetadataSchemaQuestionQualification
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import serializers, viewsets
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_condition import Or
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from django_filters import rest_framework as filters
from django.shortcuts import get_object_or_404
from applications.learning_object_metadata.serializers import (
    CommentaryListSerializer,
    CommentarySerializer,
    LearningObjectMetadataByExpet,
    LearningObjectMetadataByStudent,
    LearningObjectMetadataPopularSerializer,
    LearningObjectMetadataSerializer,
    AdminLearningObjectMetadataPublicUpdateSerializer,
    LearningObjectMetadataAllSerializer,
    LearningObjectMetadataYears,
    ROANumberPagination,
    ROANumberPaginationObservation,
    ROANumberPaginationPopular,
    ROANumberPagination_Estudent_Qualification,
    TeacherUploadListSerializer,
    LearningObjectMetadataByStudentQualification,
    LearningObjectReviewNotificationSerializer,
)
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser, IsStudentUser, IsTeacherUser
from .models import Commentary, LearningObjectMetadata
from applications.learning_object_metadata.testMailMetadata import SendEmailCreateOA_satisfay, \
    SendEmailCreateOA_not_satisfy, SendEmailCreateOA_not_satisfy_User, SendEmailCreateOA_satisfy_User, \
    SendEmailLearningObjectReviewFindings
from applications.user.models import User
from rest_framework import generics
from django.db.models import Func
from django.db.models.functions import Concat, Lower

from applications.evaluation_student.serializers import StudentEvaluationSerializer


LEARNING_OBJECT_METADATA_TAG = ['Learning Object Metadata']
LEARNING_OBJECT_SEARCH_TAG = ['Learning Object Search']
LEARNING_OBJECT_ADMIN_TAG = ['Learning Object Admin']
LEARNING_OBJECT_EVALUATION_TAG = ['Learning Object Evaluation']
LEARNING_OBJECT_INTERACTION_TAG = ['Learning Object Interaction']

LEARNING_OBJECT_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador interno usado por la ruta. Segun el endpoint puede representar un OA, un docente, un estudiante o un experto.',
)
LEARNING_OBJECT_USER_PARAMETER = OpenApiParameter(
    name='user',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador del usuario cuya evaluacion se quiere consultar.',
)
LEARNING_OBJECT_PUBLIC_PARAMETER = OpenApiParameter(
    name='public',
    type=str,
    location=OpenApiParameter.PATH,
    description='Estado de publicacion que se quiere listar. El valor llega desde la URL y se compara contra el campo `public` del OA.',
)
LEARNING_OBJECT_SEARCH_PARAMETERS = [
    OpenApiParameter('general_title', str, OpenApiParameter.QUERY, description='Busca palabras en titulo, descripcion y nombre del autor.'),
    OpenApiParameter('education_levels__id', int, OpenApiParameter.QUERY, description='Filtra por identificador del nivel educativo.'),
    OpenApiParameter('knowledge_area__id', int, OpenApiParameter.QUERY, description='Filtra por identificador del area de conocimiento.'),
    OpenApiParameter('license__value', str, OpenApiParameter.QUERY, description='Filtra por el valor tecnico de la licencia.'),
    OpenApiParameter('license__name_es', str, OpenApiParameter.QUERY, description='Filtra por el nombre en español de la licencia.'),
    OpenApiParameter('created__year', int, OpenApiParameter.QUERY, description='Filtra por anio de creacion del OA.'),
    OpenApiParameter('knowledge_area__name_es', str, OpenApiParameter.QUERY, description='Filtra por nombre en español del area de conocimiento.'),
    OpenApiParameter('education_levels__name_es', str, OpenApiParameter.QUERY, description='Filtra por nombre en español del nivel educativo.'),
    OpenApiParameter('accesibility_control', str, OpenApiParameter.QUERY, description='Parametro repetible. Acepta controles como `fullkeyboardcontrol` y `fullMouseControl`.'),
    OpenApiParameter('annotation_modeaccess', str, OpenApiParameter.QUERY, description='Parametro repetible. Acepta modos como `visual`, `text`, `auditory` o `colorDependent`.'),
    OpenApiParameter('accesibility_features', str, OpenApiParameter.QUERY, description='Parametro repetible. Acepta features como `captions`, `ttsMarkup`, `audioDescription` y `alternativeText`.'),
    OpenApiParameter('accesibility_hazard', str, OpenApiParameter.QUERY, description='Parametro repetible. Acepta hazards como `noFlashingHazard`, `FlashingHazard` y `nomotionsimulationHazard`.'),
    OpenApiParameter('is_evaluated', bool, OpenApiParameter.QUERY, description='Cuando aplica, separa OAs evaluados y no evaluados por el experto autenticado.'),
    OpenApiParameter('liked', bool, OpenApiParameter.QUERY, description='Si es `True`, prioriza OAs que tienen interacciones marcadas como like.'),
    OpenApiParameter('recent', bool, OpenApiParameter.QUERY, description='Si es `True`, ordena por fecha de creacion descendente.'),
    OpenApiParameter('scored', bool, OpenApiParameter.QUERY, description='Si es `True`, devuelve OAs con evaluacion experta visible.'),
]
LEARNING_OBJECT_ADMIN_FILTER_PARAMETERS = [
    LEARNING_OBJECT_PUBLIC_PARAMETER,
    OpenApiParameter('general_title__icontains', str, OpenApiParameter.QUERY, description='Busca OAs por coincidencia parcial del titulo, nombres o apellidos del creador.'),
    OpenApiParameter('created_init', str, OpenApiParameter.QUERY, description='Fecha inicial del rango de creacion en formato YYYY-MM-DD.'),
    OpenApiParameter('created_end', str, OpenApiParameter.QUERY, description='Fecha final del rango de creacion en formato YYYY-MM-DD.'),
]
LEARNING_OBJECT_MESSAGE_RESPONSE = inline_serializer(
    name='LearningObjectMetadataMessageResponse',
    fields={
        'message': serializers.CharField(),
        'status': serializers.IntegerField(required=False),
    },
)
LEARNING_OBJECT_TOTAL_RESPONSE = inline_serializer(
    name='LearningObjectMetadataTotalResponse',
    fields={
        'total_oa_aproved': serializers.IntegerField(),
        'toatal_oa_disapproved': serializers.IntegerField(),
    },
)
LEARNING_OBJECT_PRIORITY_REQUEST = inline_serializer(
    name='LearningObjectMetadataPriorityRequest',
    fields={
        'is_priority': serializers.ChoiceField(
            choices=['True'],
            help_text='El flujo heredado espera el texto `True` para marcar una evaluacion como prioritaria.',
        ),
    },
)


def filter_annotation_modeaccess_queryset(queryset, access_preferences):
    """Normaliza aliases del frontend y siempre devuelve un queryset valido.

    Este helper protege el filtro `annotation_modeaccess` frente a nombres
    legacy enviados por el frontend y evita que django-filter reciba `None`.
    """
    alias_map = {
        'visual': 'Visual',
        'text': 'Text',
        'auditory': 'Auditory',
        'colordependent': 'colorDependent',
        'colordepend': 'colorDependent',
    }

    normalized_preferences = []
    for preference in access_preferences:
        canonical = alias_map.get(str(preference).strip().lower())
        if canonical and canonical not in normalized_preferences:
            normalized_preferences.append(canonical)

    if not normalized_preferences:
        return queryset

    query = Q()
    for preference in normalized_preferences:
        query |= Q(annotation_modeaccess__icontains=preference)

    return queryset.filter(query)

@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Consultar OA por slug',
        description=(
            'Devuelve el detalle publico de un objeto de aprendizaje usando el slug generado al guardar la metadata. '
            'Este endpoint lo consume el frontend cuando abre la ficha individual del OA.'
        ),
        parameters=[
            OpenApiParameter(
                'slug',
                str,
                OpenApiParameter.PATH,
                description='Slug publico del objeto de aprendizaje.',
            ),
        ],
        responses={200: LearningObjectMetadataAllSerializer, 404: OpenApiResponse(description='OA no encontrado.')},
    )
)
class SlugView(RetrieveAPIView):
    """Recupera el detalle p?blico de un OA a partir de su slug."""
    lookup_field = 'slug'
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataAllSerializer

    def get_object(self):
        if getattr(self, "swagger_fake_view", False):
            raise Http404

        slug = self.kwargs['slug']
        learning_object = get_object_or_404(
            LearningObjectMetadata.objects.learningobjectBySlug(slug)
        )

        if learning_object.public:
            return learning_object

        user = self.request.user
        is_authenticated = bool(getattr(user, 'is_authenticated', False))
        is_owner = bool(is_authenticated and learning_object.user_created_id == user.id)
        administrator = getattr(user, 'administrator', None) if is_authenticated else None
        is_admin = bool(administrator is not None and getattr(administrator, 'is_active', False))
        is_superuser = bool(is_authenticated and getattr(user, 'is_superuser', False))

        if is_owner or is_admin or is_superuser:
            return learning_object

        raise Http404


class Unaccent(Func):
    """Wrapper para la función SQL `unaccent` usada en filtros de texto."""

    function = 'unaccent'


class OAFilter(filters.FilterSet):
    """Filtro principal del buscador público de objetos de aprendizaje.

    Opera sobre `LearningObjectMetadata` ya restringido a `public=True`, por lo
    que los métodos custom deben preservar el queryset recibido y no recrearlo
    desde cero.
    """
    permission_classes = [AllowAny]
    general_title = filters.CharFilter(method='general_title_filter')
    education_levels__id = filters.CharFilter(lookup_expr='iexact')
    knowledge_area__id = filters.CharFilter(lookup_expr='iexact')
    license__value = filters.CharFilter(lookup_expr='iexact')
    license__name_es = filters.CharFilter(field_name='license', lookup_expr='name_es')
    created__year = filters.CharFilter(lookup_expr='iexact')
    knowledge_area__name_es = filters.CharFilter(field_name='knowledge_area', lookup_expr='name_es')
    education_levels__name_es = filters.CharFilter(lookup_expr='iexact')
    accesibility_control = filters.CharFilter(method='accesibility_control_filter')
    annotation_modeaccess = filters.CharFilter(method='annotation_modeaccess_filter')
    accesibility_features = filters.CharFilter(method='accesibility_features_filter')
    accesibility_hazard = filters.CharFilter(method='accesibility_hazard_filter')
    is_evaluated = filters.CharFilter(method='test_and_not_tested')
    liked = filters.CharFilter(method='most_liked')
    recent = filters.CharFilter(method='most_recent')
    scored = filters.CharFilter(method='most_scored')
    class Meta:
        model = LearningObjectMetadata
        fields = [
            'general_title',
            'accesibility_control',
            'annotation_modeaccess',
            'accesibility_features',
            'accesibility_hazard',
            'education_levels__id',
            'knowledge_area__id',
            'license__value',
            'created__year',
            'education_levels',
            'knowledge_area',
            'license',
            'is_evaluated',
            'liked',
            'recent',
            'scored'
        ]

    def test_and_not_tested(self, queryset,name , value):
        """Filtra por OAs evaluados o no evaluados por el experto autenticado.

        Si la petición no viene de un experto autenticado, no aplica este
        subfiltro y conserva el queryset publico original.
        """

        is_eval = self.request.GET.get('is_evaluated')
        user = getattr(self.request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or getattr(user, 'collaboratingExpert', None) is None:
            return queryset
        if is_eval == 'True':
            query = queryset.filter(
                Q(learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id)
            ).order_by('-id')
            return query
        elif is_eval == 'False':
            query = queryset.exclude(
                learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
            ).order_by('-id')
            return query
        return queryset

    def most_liked(self,queryset, name, value):
        """Restringe el buscador a OAs con likes cuando `liked=True`."""

        key_preferences = self.request.GET.getlist('liked')
        if key_preferences[0] == 'True':
            interaction_liked = Interaction.objects.filter(liked=True)
            interactions = interaction_liked.values('learning_object_id').annotate(
                total=Count('learning_object_id')).order_by('-total')
            array_learning_objects = []
            for interaction in interactions:
                array_learning_objects.append(int(interaction.get('learning_object_id')))
            learning_object_metadata_query = queryset.filter(id__in=array_learning_objects)
            return learning_object_metadata_query

    def most_recent(self,queryset, name, value):
        """Ordena el buscador por fecha de creación cuando `recent=True`."""

        key_preferences = self.request.GET.getlist('recent')
        if key_preferences[0] == 'True':
            learning_objects_most_recent = queryset.order_by('-created')
            return learning_objects_most_recent

    def most_scored(self,queryset, name, value):
        """Restringe a OAs publicos con evaluación experta visible."""

        key_preferences = self.request.GET.getlist('scored')
        if key_preferences[0] == 'True':
            query = EvaluationCollaboratingExpert.objects.filter(
                learning_object__public=True, rating__gte=0
            ).order_by('-learning_object__id', '-rating').distinct('learning_object__id')
            learningObjectScored = []
            for learningObject in query:
                learningObjectScored.append(int(learningObject.learning_object_id))
            learning_object_metadata_query = queryset.filter(id__in=learningObjectScored)
            return learning_object_metadata_query

    def accesibility_control_filter(self, queryset, name, value):
        """Filtra por controles de accesibilidad declarados en el metadata."""

        accesibility_control = self.request.GET.getlist('accesibility_control')
        if len(accesibility_control) == 1 and 'fullkeyboardcontrol' in accesibility_control:
            return queryset.filter(
                accesibility_control__icontains='fullkeyboardcontrol'
            )
        elif len(accesibility_control) == 1 and 'fullMouseControl' in accesibility_control:
            return queryset.filter(
                accesibility_control__icontains='fullMouseControl'
            )
        elif len(
                accesibility_control) == 2 and 'fullMouseControl' in accesibility_control and 'fullkeyboardcontrol' in accesibility_control:
            return queryset.filter(
                Q(accesibility_control__icontains='fullkeyboardcontrol') |
                Q(accesibility_control__icontains='fullMouseControl')

            )

    def annotation_modeaccess_filter(self, queryset, name, value):
        """Filtra por modos de acceso usando valores canónicos del helper."""

        access_preferences = self.request.GET.getlist('annotation_modeaccess')
        return filter_annotation_modeaccess_queryset(queryset, access_preferences)

    def accesibility_hazard_filter(self, queryset, name, value):
        """Filtra por hazards de accesibilidad declarados por el OA."""

        hazard_preferences = self.request.GET.getlist('accesibility_hazard')
        if len(hazard_preferences) == 1 and 'noFlashingHazard' in hazard_preferences:
            return queryset.filter(
                accesibility_hazard__icontains='noFlashingHazard'
            )
        elif len(hazard_preferences) == 1 and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='FlashingHazard')
            )
        elif len(hazard_preferences) == 1 and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )
        elif len(
                hazard_preferences) == 2 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='noFlashingHazard') |
                Q(accesibility_hazard__icontains='FlashingHazard')
            )
        elif len(
                hazard_preferences) == 2 and 'noFlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='noFlashingHazard') |
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )
        elif len(
                hazard_preferences) == 2 and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='FlashingHazard') |
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )
        elif len(
                hazard_preferences) == 3 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='noFlashingHazard') |
                Q(accesibility_hazard__icontains='FlashingHazard') |
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )

    def accesibility_features_filter(self, queryset, name, value):
        """Filtra por combinaciones de features de accesibilidad."""

        access_preferences = self.request.GET.getlist('accesibility_features')
        if len(access_preferences) == 1 and 'captions' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='captions'
            )
        if len(access_preferences) == 1 and 'ttsMarkup' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='ttsMarkup'
            )
        if len(access_preferences) == 1 and 'audioDescription' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='audioDescription'
            )
        if len(access_preferences) == 1 and 'alternativeText' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='alternativeText'
            )
        if len(access_preferences) == 2 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup')
            )
        if len(access_preferences) == 2 and 'captions' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='audioDescription')
            )
        if len(access_preferences) == 2 and 'captions' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 2 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription')
            )
        if len(access_preferences) == 2 and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 2 and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription')
            )
        if len(access_preferences) == 3 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 3 and 'captions' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 4 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )

    def general_title_filter(self, queryset, name, value):
        """Busca palabras clave en título, descripción y nombre del autor."""

        general_reference_search = self.request.GET.getlist('general_title')

        if len(general_reference_search) == 1:
            keywords = general_reference_search[0].split()
            queries = [Q(general_title__icontains=keyword)
                       | Q(general_description__icontains=keyword)
                       | Q(user_created__first_name__icontains=keyword)
                       | Q(user_created__last_name__icontains=keyword) for keyword in keywords]

            q_object = queries.pop()
            for query in queries:
                q_object |= query

            return queryset.filter(
               q_object
            )


class OAFilterExpert(filters.FilterSet):
    """Filtros del buscador usado por expertos sobre OAs ya evaluados."""
    permission_classes = [AllowAny]
    general_title = filters.CharFilter(lookup_expr='icontains')
    education_levels__description = filters.CharFilter(lookup_expr='iexact')
    knowledge_area__name = filters.CharFilter(lookup_expr='iexact')
    license__description = filters.CharFilter(lookup_expr='iexact')
    created__year = filters.CharFilter(lookup_expr='iexact')
    is_evaluated = filters.CharFilter(method='is_evaluated_filter')
    key_preferences = filters.CharFilter(method='key_preferences_filter')
    annotation_modeaccess = filters.CharFilter(method='annotation_modeaccess_filter')
    accesibility_features = filters.CharFilter(method='accesibility_features_filter')
    accesibility_hazard = filters.CharFilter(method='accesibility_hazard_filter')

    class Meta:
        model = LearningObjectMetadata
        fields = [
            'is_evaluated',
            'general_title',
            'key_preferences',
            'annotation_modeaccess',
            'accesibility_features',
            'accesibility_hazard',
            'education_levels__description',
            'knowledge_area__name',
            'license__description',
            'created__year'
        ]

    def is_evaluated_filter(self, queryset, name, value):
        """Mantiene el queryset del experto sin transformaciones adicionales.

        La decisión real entre evaluados y no evaluados se resuelve en la
        vista `SerachAPIViewExpert.get_queryset()`.
        """

        query = queryset.all()
        return query

    def key_preferences_filter(self, queryset, name, value):
        """Filtra por controles de accesibilidad en el buscador de experto."""

        key_preferences = self.request.GET.getlist('key_preferences')
        if len(key_preferences) == 1 and 'fullkeyboardcontrol' in key_preferences:
            return queryset.filter(
                accesibility_control__icontains='fullkeyboardcontrol'
            )
        elif len(key_preferences) == 1 and 'fullMouseControl' in key_preferences:
            return queryset.filter(
                accesibility_control__icontains='fullMouseControl'
            )
        elif len(
                key_preferences) == 2 and 'fullMouseControl' in key_preferences and 'fullkeyboardcontrol' in key_preferences:
            return queryset.filter(
                Q(accesibility_control__icontains='fullkeyboardcontrol') |
                Q(accesibility_control__icontains='fullMouseControl')

            )

    def annotation_modeaccess_filter(self, queryset, name, value):
        """Filtra por modos de acceso usando valores canónicos del helper."""

        access_preferences = self.request.GET.getlist('annotation_modeaccess')
        return filter_annotation_modeaccess_queryset(queryset, access_preferences)

    def accesibility_hazard_filter(self, queryset, name, value):
        """Filtra por hazards de accesibilidad en el buscador de experto."""

        hazard_preferences = self.request.GET.getlist('accesibility_hazard')
        if len(hazard_preferences) == 1 and 'noFlashingHazard' in hazard_preferences:
            return queryset.filter(
                accesibility_hazard__icontains='noFlashingHazard'
            )
        elif len(hazard_preferences) == 1 and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='FlashingHazard')
            )
        elif len(hazard_preferences) == 1 and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )
        elif len(
                hazard_preferences) == 2 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='noFlashingHazard') |
                Q(accesibility_hazard__icontains='FlashingHazard')
            )
        elif len(
                hazard_preferences) == 2 and 'noFlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='noFlashingHazard') |
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )
        elif len(
                hazard_preferences) == 2 and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='FlashingHazard') |
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )
        elif len(
                hazard_preferences) == 3 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
                Q(accesibility_hazard__icontains='noFlashingHazard') |
                Q(accesibility_hazard__icontains='FlashingHazard') |
                Q(accesibility_hazard__icontains='nomotionsimulationHazard')
            )

    def accesibility_features_filter(self, queryset, name, value):
        """Filtra por combinaciones de features de accesibilidad."""

        access_preferences = self.request.GET.getlist('accesibility_features')
        if len(access_preferences) == 1 and 'captions' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='captions'
            )
        if len(access_preferences) == 1 and 'ttsMarkup' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='ttsMarkup'
            )
        if len(access_preferences) == 1 and 'audioDescription' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='audioDescription'
            )
        if len(access_preferences) == 1 and 'alternativeText' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains='alternativeText'
            )
        if len(access_preferences) == 2 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup')
            )
        if len(access_preferences) == 2 and 'captions' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='audioDescription')
            )
        if len(access_preferences) == 2 and 'captions' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 2 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription')
            )
        if len(access_preferences) == 2 and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 2 and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription')
            )
        if len(access_preferences) == 3 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 3 and 'captions' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )
        if len(access_preferences) == 4 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
                Q(accesibility_features__icontains='captions') |
                Q(accesibility_features__icontains='ttsMarkup') |
                Q(accesibility_features__icontains='audioDescription') |
                Q(accesibility_features__icontains='alternativeText')
            )


class LearningObjectPublicAndPrivateFilter(filters.FilterSet):
    """Filtro administrativo para OAs aprobados y pendientes.

    Mantiene el parametro heredado `general_title__icontains`, pero amplia la
    busqueda a nombres y apellidos del usuario creador para no romper el
    contrato actual del frontend.
    """

    general_title__icontains = filters.CharFilter(method='filter_text')

    class Meta:
        model = LearningObjectMetadata
        fields = []

    def filter_text(self, queryset, name, value):
        queryset = queryset.annotate(
            user_created_full_name=Concat(
                'user_created__first_name',
                Value(' '),
                'user_created__last_name',
            )
        )
        return queryset.filter(
            Q(general_title__icontains=value)
            | Q(user_created__first_name__icontains=value)
            | Q(user_created__last_name__icontains=value)
            | Q(user_created_full_name__icontains=value)
        ).distinct()


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_SEARCH_TAG,
        summary='Buscar objetos de aprendizaje publicos',
        description=(
            'Lista OAs aprobados (`public=True`) y permite aplicar filtros de texto, catalogos, fecha, '
            'accesibilidad, popularidad, evaluacion y orden reciente. La respuesta usa la paginacion principal del ROA.'
        ),
        parameters=LEARNING_OBJECT_SEARCH_PARAMETERS,
        responses={200: LearningObjectMetadataAllSerializer(many=True)},
    )
)
class SerachAPIView(ListAPIView):
    """Buscador publico principal de objetos de aprendizaje aprobados."""
    permission_classes = [AllowAny]
    queryset = LearningObjectMetadata.objects.filter(public=True).order_by('-pk')
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    filter_class = OAFilter


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_SEARCH_TAG,
        summary='Buscar OAs para evaluacion experta',
        description=(
            'Lista objetos de aprendizaje para el experto autenticado. El parametro `is_evaluated` permite separar '
            'los OAs que ya evaluo de los que siguen pendientes para ese experto.'
        ),
        parameters=LEARNING_OBJECT_SEARCH_PARAMETERS,
        responses={
            200: LearningObjectMetadataAllSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='El usuario no tiene rol de experto colaborador.'),
        },
    )
)
class SerachAPIViewExpert(ListAPIView):
    """Buscador de OAs evaluados o no evaluados para el experto autenticado."""
    permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    filter_class = OAFilterExpert

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LearningObjectMetadata.objects.none()
        is_eval = self.request.GET.get('is_evaluated')
        if is_eval == 'True':
            query = LearningObjectMetadata.objects.filter(
                Q(learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id)
            ).exclude(
                public=False
            ).order_by('-id')
            return query
        elif is_eval == 'False':
            query = LearningObjectMetadata.objects.filter(
            ).exclude(
                Q(public=False) and Q(
                    learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id)
            ).order_by('-id')
            return query


class OAEvaluadedFilter(django_filters.FilterSet):
    """Filtros sobre resultados de evaluación experta por pregunta."""

    permission_classes = [AllowAny]
    general_title = filters.CharFilter(method='title_filter')
    education_levels__description = filters.CharFilter(method='education_level_filter')
    knowledge_area__name = filters.CharFilter(method='knowledge_area_name_filter')
    preferences__description = filters.CharFilter(method='preferences_description_filter')
    license__description = filters.CharFilter(method='license_description_filter')
    created__year = filters.CharFilter(method='created_year_filter')

    class Meta:
        model = EvaluationQuestionsQualification
        fields = [
            'general_title',
            'education_levels__description',
            'knowledge_area__name',
            'preferences__description',
            'license__description',
            'created__year'
        ]

    def title_filter(self, queryset, name, value):
        """Filtra resultados por título del OA evaluado."""

        return queryset.filter(
            concept_evaluations__evaluation_collaborating_expert__learning_object__general_title__icontains=value
        )

    def education_level_filter(self, queryset, name, value):
        """Filtra resultados por nivel educativo del OA evaluado."""

        return queryset.filter(
            concept_evaluations__evaluation_collaborating_expert__learning_object__education_levels__description__iexact=value
        )

    def knowledge_area_name_filter(self, queryset, name, value):
        """Filtra resultados por área de conocimiento del OA evaluado."""

        return queryset.filter(
            concept_evaluations__evaluation_collaborating_expert__learning_object__knowledge_area__name__iexact=value
        )

    def license_description_filter(self, queryset, name, value):
        """Filtra resultados por licencia del OA evaluado."""

        return queryset.filter(
            concept_evaluations__evaluation_collaborating_expert__learning_object__license__description__iexact=value
        )

    def created_year_filter(self, queryset, name, value):
        """Filtra resultados por año de creación del OA evaluado."""

        return queryset.filter(
            concept_evaluations__evaluation_collaborating_expert__learning_object__created__year__iexact=value
        )

    def preferences_description_filter(self, queryset, name, value):
        """Filtra por concepto de evaluación asociado a la pregunta."""

        return queryset.filter(
            evaluation_question__evaluation_concept__concept__iexact=value
        )


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Buscar OAs evaluados por preguntas expertas',
        description=(
            'Consulta resultados de evaluacion experta usando filtros sobre el OA, sus catalogos y los conceptos '
            'de evaluacion asociados a cada pregunta.'
        ),
        parameters=[
            OpenApiParameter('general_title', str, OpenApiParameter.QUERY, description='Busca por titulo del OA evaluado.'),
            OpenApiParameter('education_levels__description', str, OpenApiParameter.QUERY, description='Filtra por descripcion del nivel educativo.'),
            OpenApiParameter('knowledge_area__name', str, OpenApiParameter.QUERY, description='Filtra por nombre del area de conocimiento.'),
            OpenApiParameter('preferences__description', str, OpenApiParameter.QUERY, description='Filtra por concepto de evaluacion asociado a la pregunta.'),
            OpenApiParameter('license__description', str, OpenApiParameter.QUERY, description='Filtra por descripcion de la licencia.'),
            OpenApiParameter('created__year', int, OpenApiParameter.QUERY, description='Filtra por anio de creacion del OA.'),
        ],
        responses={200: QuestionQualificationSearchSerializer(many=True)},
    )
)
class SerachEvaluatedAPIView(ListAPIView):
    """Busca OAs evaluados a partir de sus calificaciones por pregunta."""
    permission_classes = [AllowAny]
    queryset = EvaluationQuestionsQualification.objects.filter(
        concept_evaluations__evaluation_collaborating_expert__learning_object__public=True,
    ).order_by(
        '-concept_evaluations__evaluation_collaborating_expert__learning_object__id'
    ).distinct('concept_evaluations__evaluation_collaborating_expert__learning_object__id')
    serializer_class = QuestionQualificationSearchSerializer
    pagination_class = ROANumberPagination
    filter_class = OAEvaluadedFilter


@extend_schema_view(
    list=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Listar metadata visible para el usuario',
        description=(
            'Devuelve la metadata de OAs disponible para el usuario autenticado o anonimo segun las reglas del manager. '
            'El listado usa la salida completa porque el frontend muestra datos de catalogos, archivo, rating y banderas de evaluacion.'
        ),
        responses={200: LearningObjectMetadataAllSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Consultar metadata por identificador',
        description='Recupera un OA concreto aplicando la visibilidad definida en el manager de metadata.',
        responses={200: LearningObjectMetadataAllSerializer, 404: OpenApiResponse(description='Metadata no encontrada o no visible.')},
    ),
    create=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Crear metadata de un OA',
        description=(
            'Registra la metadata creada por un docente. Despues de guardar dispara la evaluacion inicial del OA, '
            'que puede publicar, rechazar o dejar pendiente el recurso segun las reglas heredadas.'
        ),
        request=LearningObjectMetadataSerializer,
        responses={201: LearningObjectMetadataSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Actualizar metadata de un OA',
        description='Actualiza de forma completa la metadata del OA usando el serializer base de escritura.',
        request=LearningObjectMetadataSerializer,
        responses={200: LearningObjectMetadataSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Actualizar parcialmente metadata de un OA',
        description='Permite modificar solo algunos campos de la metadata del OA.',
        request=LearningObjectMetadataSerializer,
        responses={200: LearningObjectMetadataSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Eliminar metadata de un OA',
        description='Elimina la metadata del OA cuando pertenece al docente autenticado.',
        responses={200: LEARNING_OBJECT_MESSAGE_RESPONSE, 404: OpenApiResponse(description='Metadata no encontrada o sin permisos.')},
    ),
)
class LearningObjectMetadataViewSet(viewsets.ModelViewSet):
    """CRUD principal de metadata asociado al docente propietario del OA.

    Las operaciones de escritura quedan restringidas a docentes autenticados.
    Al crear metadata se dispara inmediatamente el flujo de evaluación
    automática o manual según el tipo de OA cargado.
    """

    def get_permissions(self):
        if (self.action == 'list' or self.action == 'retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsTeacherUser]
        return [permission() for permission in permission_classes]

    serializer_class = LearningObjectMetadataSerializer
    queryset = LearningObjectMetadata.objects.all()

    @transaction.atomic
    def perform_create(self, serializer):
        """Guarda la metadata y lanza la evaluación inicial del OA."""
        serializer.save(
            user_created=self.request.user
        )
        automaticEvaluation(serializer.data['id'])

    def list(self, request):
        """Lista la metadata visible para el usuario actual."""
        user = self.request.user
        queryset = LearningObjectMetadata.objects.learning_object_metadata_by_user(user)
        serializer = LearningObjectMetadataAllSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera la metadata visible para el usuario actual por `pk`."""
        user = self.request.user
        queryset = LearningObjectMetadata.objects.learning_object_metadata_retrieve_by_user(user, pk)
        serializer = LearningObjectMetadataAllSerializer(queryset)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """Elimina la metadata del OA perteneciente al docente autenticado."""
        user = self.request.user
        LearningObjectMetadata.objects.learning_object_metadata_by_user_destroy(user, pk)
        return Response({"message": "success"}, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_ADMIN_TAG,
        summary='Listar OAs por estado de publicacion',
        description=(
            'Lista objetos de aprendizaje aprobados o no aprobados para revision administrativa. '
            'Puede filtrarse por titulo y por rango de fechas de creacion.'
        ),
        parameters=LEARNING_OBJECT_ADMIN_FILTER_PARAMETERS,
        responses={
            200: LearningObjectMetadataAllSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListLearningObjectPublicAndPrivate(ListAPIView):
    """Lista OAs públicos o privados para revisión administrativa."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    lookup_field = "public"
    filter_backends = [DjangoFilterBackend]
    filterset_class = LearningObjectPublicAndPrivateFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LearningObjectMetadata.objects.none()
        date_init = self.request.query_params.get("created_init")
        date_end = self.request.query_params.get("created_end")
        public = self.kwargs['public']
        if date_init is None or date_end is None:
            return LearningObjectMetadata.objects.filter(public=public).order_by('-pk')

        date_init = datetime.strptime(date_init, '%Y-%m-%d').date()
        date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        return LearningObjectMetadata.objects.filter(public=public, created__date__range=[date_init, date_end]).order_by(
            '-pk')


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_ADMIN_TAG,
        summary='Consultar OA antes de cambiar publicacion',
        description='Devuelve la metadata completa del OA que el administrador puede aprobar o retirar del catalogo publico.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={200: LearningObjectMetadataAllSerializer, 404: OpenApiResponse(description='OA no encontrado.')},
    ),
    put=extend_schema(
        tags=LEARNING_OBJECT_ADMIN_TAG,
        summary='Actualizar estado publico de un OA',
        description='Actualiza el campo `public` del objeto de aprendizaje desde el panel administrativo.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        request=AdminLearningObjectMetadataPublicUpdateSerializer,
        responses={200: LearningObjectMetadataAllSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    patch=extend_schema(
        tags=LEARNING_OBJECT_ADMIN_TAG,
        summary='Actualizar parcialmente estado publico de un OA',
        description='Permite cambiar solo el campo `public` sin reenviar toda la metadata.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        request=AdminLearningObjectMetadataPublicUpdateSerializer,
        responses={200: LearningObjectMetadataAllSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class UpdatePublicLearningObject(RetrieveUpdateAPIView):
    """Permite cambiar el estado público de un OA desde administración."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataAllSerializer
    queryset = LearningObjectMetadata.objects.all()


@extend_schema_view(
    post=extend_schema(
        tags=LEARNING_OBJECT_ADMIN_TAG,
        summary='Notificar hallazgos administrativos de un OA',
        description=(
            'Permite a un administrador activo o superusuario enviar por correo al docente creador '
            'los hallazgos o cambios solicitados sobre un objeto de aprendizaje.'
        ),
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        request=LearningObjectReviewNotificationSerializer,
        responses={
            200: LEARNING_OBJECT_MESSAGE_RESPONSE,
            400: OpenApiResponse(description='Payload invalido o el OA no tiene un docente notificable.'),
            404: OpenApiResponse(description='OA no encontrado.'),
        },
    )
)
class LearningObjectReviewNotificationAPIView(APIView):
    """Envía al docente los hallazgos administrativos detectados en su OA."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def post(self, request, pk, *args, **kwargs):
        serializer = LearningObjectReviewNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        learning_object = get_object_or_404(LearningObjectMetadata, pk=pk)
        teacher_user = learning_object.user_created
        teacher_email = (getattr(teacher_user, 'email', '') or '').strip()

        if teacher_user is None or not teacher_email:
            return Response(
                {'message': 'The learning object has no teacher email to notify.', 'status': 400},
                status=HTTP_400_BAD_REQUEST,
            )

        teacher_name = f"{teacher_user.first_name} {teacher_user.last_name}".strip() or teacher_email

        mail_learning_object_findings.sendMailFindings(
            teacher_email,
            teacher_name,
            learning_object.general_title,
            serializer.validated_data['message'],
        )

        return Response(
            {'message': 'Notification sent successfully', 'status': HTTP_200_OK},
            status=HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Contar OAs aprobados y no aprobados',
        description=(
            'Devuelve los contadores globales de objetos de aprendizaje publicados y no publicados. '
            'Los nombres de campos conservan la escritura heredada que ya consume el frontend.'
        ),
        responses={200: LEARNING_OBJECT_TOTAL_RESPONSE},
    )
)
class TotalLearningObjectAproved(APIView):
    """Devuelve contadores globales de OAs aprobados y pendientes."""
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        learning_approved = LearningObjectMetadata.objects.filter(
            public=True,
        ).count()
        learning_disapproved = LearningObjectMetadata.objects.filter(
            public=False,
        ).count()
        result = {
            "total_oa_aproved": learning_approved,
            "toatal_oa_disapproved": learning_disapproved,
        }
        return Response(result, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Listar OAs populares',
        description='Devuelve hasta cuatro OAs publicos ordenados por la evaluacion experta visible.',
        responses={200: LearningObjectMetadataPopularSerializer(many=True)},
    )
)
class ListLearningObjectPopular(ListAPIView):
    """Lista los OAs públicos mejor valorados por evaluación experta."""
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataPopularSerializer

    pagination_class = None

    def get_queryset(self):
        ranked_evaluations = EvaluationCollaboratingExpert.objects.filter(
            learning_object__public=True,
            rating__gte=0,
        ).order_by('-rating', '-learning_object__created', '-learning_object_id', '-id').values_list(
            'id',
            'learning_object_id',
        )

        selected_evaluation_ids = []
        selected_learning_object_ids = set()
        for evaluation_id, learning_object_id in ranked_evaluations:
            if learning_object_id in selected_learning_object_ids:
                continue
            selected_evaluation_ids.append(evaluation_id)
            selected_learning_object_ids.add(learning_object_id)
            if len(selected_evaluation_ids) == 4:
                break

        if not selected_evaluation_ids:
            return EvaluationCollaboratingExpert.objects.none()

        order_by_rank = Case(
            *[
                When(id=evaluation_id, then=position)
                for position, evaluation_id in enumerate(selected_evaluation_ids)
            ],
            output_field=IntegerField(),
        )
        return EvaluationCollaboratingExpert.objects.filter(
            id__in=selected_evaluation_ids,
        ).select_related('learning_object').order_by(order_by_rank)


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Listar OAs recientes para portada',
        description='Devuelve un bloque corto de OAs publicos recientes para secciones principales del frontend.',
        responses={200: LearningObjectMetadataAllSerializer(many=True)},
    )
)
class ListLearningObjectAlls(ListAPIView):
    """Lista un bloque corto de OAs públicos para la página principal."""
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataAllSerializer

    pagination_class = None

    def get_queryset(self):
        query = LearningObjectMetadata.objects.filter(
            public=True
        ).order_by('-id')[:8]
        return query


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Listar evaluaciones realizadas por un experto',
        description='Devuelve las evaluaciones expertas registradas por el experto indicado en la URL.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={
            200: LearningObjectMetadataByExpet(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListLearningObjectEvaluatedByExpert(ListAPIView):
    """Lista evaluaciónes expertas realizadas por un experto concreto."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataByExpet
    pagination_class = ROANumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EvaluationCollaboratingExpert.objects.none()
        id = self.kwargs['id']
        query = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Listar evaluaciones expertas de un OA',
        description='Devuelve las evaluaciones realizadas por expertos sobre el objeto de aprendizaje indicado.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={
            200: LearningObjectMetadataByExpet(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListLearningObjectEvaluatedByExpertQualifications(ListAPIView):
    """Lista evaluaciónes expertas asociadas a un OA concreto."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataByExpet
    pagination_class = ROANumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EvaluationCollaboratingExpert.objects.none()
        id = self.kwargs['id']
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object_id=id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Consultar evaluacion experta',
        description='Devuelve una evaluacion experta concreta antes de marcarla como prioritaria.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={200: LearningObjectMetadataByExpet, 404: OpenApiResponse(description='Evaluacion no encontrada.')},
    ),
    put=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Marcar evaluacion experta como prioritaria',
        description=(
            'Actualiza la evaluacion experta indicada para dejarla como prioritaria. '
            'Antes de activarla, el flujo heredado desmarca la evaluacion que estuviera priorizada.'
        ),
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        request=LEARNING_OBJECT_PRIORITY_REQUEST,
        responses={
            200: LEARNING_OBJECT_MESSAGE_RESPONSE,
            400: LEARNING_OBJECT_MESSAGE_RESPONSE,
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    ),
    patch=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Marcar parcialmente evaluacion experta como prioritaria',
        description='Mismo flujo de prioridad que PUT, conservado para clientes que envian PATCH.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        request=LEARNING_OBJECT_PRIORITY_REQUEST,
        responses={200: LEARNING_OBJECT_MESSAGE_RESPONSE, 400: LEARNING_OBJECT_MESSAGE_RESPONSE},
    ),
)
class ListLearningObjectExpertQualificationsUpdate(generics.RetrieveUpdateAPIView):
    """Permite marcar una evaluación experta como prioritaria.

    El flujo heredado asume que solo una evaluación puede quedar con
    `is_priority=True` a la vez.
    """

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataByExpet

    def update(self, request, pk=None):
        query_old_priority = EvaluationCollaboratingExpert.objects.filter(
            is_priority=True
        )

        if len(query_old_priority) == 1:
            query_old_priority[0].is_priority = False
            query_old_priority[0].save()
            get_new_query = EvaluationCollaboratingExpert.objects.get(id=pk)
            if request.data['is_priority'] == "True":
                get_new_query.is_priority = True
                get_new_query.save()
                return Response({"message": "success", "status": 200}, status=HTTP_200_OK)
            return Response({"message": "error", "status": 400}, status=HTTP_400_BAD_REQUEST)

        if len(query_old_priority) == 0:
            get_new_query = EvaluationCollaboratingExpert.objects.get(id=pk)
            if request.data['is_priority'] == "True":
                get_new_query.is_priority = True
                get_new_query.save()
                return Response({"message": "success", "status": 200}, status=HTTP_200_OK)
            return Response({"message": "error", "status": 400}, status=HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Listar evaluaciones realizadas por un estudiante',
        description='Devuelve las evaluaciones estudiantiles registradas por el estudiante indicado en la URL.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={
            200: LearningObjectMetadataByStudent(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListLearningObjectEvaluatedByStudent(ListAPIView):
    """Lista evaluaciónes estudiantiles realizadas por un estudiante concreto."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataByStudent
    pagination_class = ROANumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentEvaluation.objects.none()
        id = self.kwargs['id']
        query = StudentEvaluation.objects.filter(
            student__student__id=id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Listar evaluaciones estudiantiles de un OA',
        description='Devuelve las calificaciones estudiantiles asociadas al objeto de aprendizaje indicado.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={
            200: LearningObjectMetadataByStudentQualification(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListLearningObjectEvaluatedByStudentQualification(ListAPIView):
    """Lista evaluaciónes estudiantiles asociadas a un OA concreto."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataByStudentQualification
    pagination_class = ROANumberPagination_Estudent_Qualification

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentEvaluation.objects.none()
        id = self.kwargs['id']
        query = StudentEvaluation.objects.filter(
            learning_object_id=id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Consultar evaluacion estudiantil de un usuario sobre un OA',
        description='Devuelve la evaluacion que un usuario estudiante registro para el objeto de aprendizaje indicado.',
        parameters=[LEARNING_OBJECT_USER_PARAMETER, LEARNING_OBJECT_ID_PARAMETER],
        responses={
            200: EvaluationStudentList_EvaluationSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListEvaluatedToStudentRetriveAPIView(ListAPIView):
    """Recupera la evaluación estudiantil de un usuario para un OA concreto."""
    permission_classes = [IsAuthenticated, (IsAdministratorUser)]
    serializer_class = EvaluationStudentList_EvaluationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentEvaluation.objects.none()
        id = self.kwargs['id']
        user_id = self.kwargs['user']
        return StudentEvaluation.objects.filter(
            student__id=user_id,
            learning_object__id=id,
        ).distinct('learning_object')


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Consultar evaluacion experta de un usuario sobre un OA',
        description='Devuelve la evaluacion que un experto registro para el objeto de aprendizaje indicado.',
        parameters=[LEARNING_OBJECT_USER_PARAMETER, LEARNING_OBJECT_ID_PARAMETER],
        responses={
            200: EvaluationCollaboratingExpertEvaluationSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListOAEvaluatedToExpertRetriveAPIView(ListAPIView):
    """Recupera la evaluación experta de un usuario para un OA concreto."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EvaluationCollaboratingExpert.objects.none()
        id = self.kwargs['id']
        user_id = self.kwargs['user']
        query = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__id=user_id,
            learning_object__id=id,
        ).distinct('learning_object')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_ADMIN_TAG,
        summary='Listar OAs cargados por un docente',
        description='Devuelve los objetos de aprendizaje subidos por el docente indicado para revision administrativa.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={
            200: LearningObjectMetadataAllSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class ListLearningObjectUploadByTeacher(ListAPIView):
    """Lista los OAs cargados por un docente para revisión administrativa."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LearningObjectMetadata.objects.none()
        id = self.kwargs['id']
        query = LearningObjectMetadata.objects.filter(
            user_created__teacher__id=id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Listar anios disponibles de OAs',
        description='Devuelve los anios de creacion presentes entre objetos de aprendizaje publicos.',
        responses={200: LearningObjectMetadataYears(many=True)},
    )
)
class ListLearningObjecYears(ListAPIView):
    """Lista años de creación disponibles entre OAs públicos."""
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataYears
    pagination_class = None

    def get_queryset(self):
        query = LearningObjectMetadata.objects.filter(
            public=True
        ).distinct('created__year')
        return query


@extend_schema_view(
    list=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Listar comentarios propios',
        description='Lista los comentarios creados por el usuario autenticado.',
        responses={200: CommentarySerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Consultar comentario propio',
        description='Devuelve un comentario siempre que pertenezca al usuario autenticado.',
        responses={200: CommentarySerializer, 404: OpenApiResponse(description='Comentario no encontrado para el usuario.')},
    ),
    create=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Crear comentario sobre un OA',
        description='Registra un comentario y lo asocia automaticamente al usuario autenticado.',
        request=CommentarySerializer,
        responses={201: CommentarySerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Actualizar comentario',
        description='Actualiza completamente un comentario registrado sobre un OA.',
        request=CommentarySerializer,
        responses={200: CommentarySerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Actualizar parcialmente comentario',
        description='Permite modificar solo algunos campos del comentario.',
        request=CommentarySerializer,
        responses={200: CommentarySerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Eliminar comentario',
        description='Elimina un comentario creado sobre un OA.',
        responses={204: OpenApiResponse(description='Comentario eliminado.')},
    ),
)
class CommentaryModelView(viewsets.ModelViewSet):
    """CRUD de comentarios para usuarios autenticados con rol operativo."""

    permission_classes = [IsAuthenticated, Or(IsTeacherUser, IsStudentUser, IsCollaboratingExpertUser)]
    serializer_class = CommentarySerializer
    queryset = Commentary.objects.all()

    def perform_create(self, serializer):
        """Asocia el comentario al usuario autenticado al momento de crearlo."""
        serializer.save(
            user=self.request.user
        )

    def retrieve(self, request, pk=None):
        """Recupera un comentario propio por identificador."""
        queryset = Commentary.objects.filter(
            user__id=self.request.user.id
        )
        comment = get_object_or_404(queryset, pk=pk)
        serializer = CommentarySerializer(comment)
        return Response(serializer.data, status=HTTP_200_OK)

    def list(self, request):
        """Lista los comentarios creados por el usuario autenticado."""
        queryset = Commentary.objects.filter(
            user__id=self.request.user.id
        )
        serializer = CommentarySerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Listar comentarios visibles de un OA',
        description='Devuelve comentarios asociados al objeto de aprendizaje indicado. Esta ruta es publica y usa paginacion compacta.',
        parameters=[LEARNING_OBJECT_ID_PARAMETER],
        responses={200: CommentaryListSerializer(many=True)},
    )
)
class CommentaryListAPIView(ListAPIView):
    """Lista los comentarios visibles asociados a un OA."""
    permission_classes = [AllowAny]
    serializer_class = CommentaryListSerializer
    pagination_class = ROANumberPaginationPopular

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Commentary.objects.none()
        id = self.kwargs['pk']
        return Commentary.objects.filter(
            learning_object__id=id
        )


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_INTERACTION_TAG,
        summary='Listar OAs vistos por el usuario',
        description='Devuelve OAs asociados a interacciones de visualizacion del usuario autenticado, mostrando la evaluacion experta visible.',
        responses={
            200: LearningObjectMetadataPopularSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='El rol del usuario no puede consultar este recurso.'),
        },
    )
)
class LearningObjectMetadataViewedAPIView(ListAPIView):
    """Lista OAs ya vistos por el usuario con su evaluación experta visible."""
    permission_classes = [IsAuthenticated, (IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser)]
    serializer_class = LearningObjectMetadataPopularSerializer
    pagination_class = ROANumberPaginationPopular

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EvaluationCollaboratingExpert.objects.none()
        query = list(Interaction.objects.filter(user=self.request.user))
        oa_list_viewed = []
        for q in query:
            oa_list_viewed.append(q.learning_object.id)
        queryset = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id__in=oa_list_viewed
        ).order_by('-learning_object__id').distinct('learning_object__id')
        return queryset


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Listar OAs cargados por el usuario autenticado',
        description='Devuelve los objetos de aprendizaje creados por el usuario actual junto con rating y observacion principal.',
        responses={
            200: TeacherUploadListSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='El rol del usuario no puede consultar este recurso.'),
        },
    )
)
class LearningObjectTecherListAPIView(ListAPIView):
    """Lista los OAs cargados por el usuario autenticado."""
    permission_classes = [IsAuthenticated, (IsTeacherUser | IsStudentUser | IsCollaboratingExpertUser)]
    serializer_class = TeacherUploadListSerializer
    pagination_class = ROANumberPaginationObservation

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LearningObjectMetadata.objects.none()
        queryset = LearningObjectMetadata.objects.filter(
            user_created=self.request.user
        ).order_by('-created')
        return queryset


@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_EVALUATION_TAG,
        summary='Listar OAs calificados por el estudiante autenticado',
        description='Devuelve objetos de aprendizaje que el estudiante autenticado ya evaluo.',
        responses={
            200: TeacherUploadListSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol estudiante.'),
        },
    )
)
class LearningObjectStudentQualificationAPIView(ListAPIView):
    """Lista los OAs que el estudiante autenticado ya calificó."""
    permission_classes = [IsAuthenticated, IsStudentUser]
    serializer_class = TeacherUploadListSerializer
    pagination_class = ROANumberPaginationPopular

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LearningObjectMetadata.objects.none()
        queryset = LearningObjectMetadata.objects.filter(
            student_learning_objects__student_id=self.request.user.id
        )
        return queryset

# Estos servicios de correo se inicializan una sola vez y se reutilizan para
# notificar aprobación o rechazo automático del OA.
mail_upload_OA_Satisfy = SendEmailCreateOA_satisfay()
mail_upload_OA_Not_Satisfy = SendEmailCreateOA_not_satisfy()
mail_upload_OA_Not_Satisfy_User = SendEmailCreateOA_not_satisfy_User()
mail_upload_OA_Satisfy_User = SendEmailCreateOA_satisfy_User()
mail_learning_object_findings = SendEmailLearningObjectReviewFindings()
LEARNING_OBJECT_REVIEW_EMAIL = 'edutech@ups.edu.ec'
LEARNING_OBJECT_REVIEW_NAME = 'Edutech UPS'


def automaticEvaluation(id):
    """Decide el flujo de evaluación de metadata segun el tipo de OA cargado."""
    META = LearningObjectMetadata.objects.get(id=id)
    if META.is_adapted_oer:
        objeto = MetadataAutomaticEvaluation.objects.create(
            learning_object=META,
            rating_schema=0.0
        )
        objeto.save()

        for i in EvaluationConcept.objects.all():
            concept = MetadataQualificationConcept.objects.create(
                evaluation_concept=i,
                evaluation_automatic_evaluation=objeto,
                average_schema=0.0
            )
            concept.save()

        automatic_evaluation_metadata_learning_object(objeto, META)
    else:
        manual_evaluation_metada_learning_object(META)


def automatic_evaluation_metadata_learning_object(objeto, META):
    """Evalúa metadata adaptada usando esquemas automáticos por concepto.

    Si el puntaje final alcanza el umbral heredado, el OA se publica y se
    notifica a administradores. En caso contrario se notifica rechazo al
    docente y a administración.
    """

    dato = 0
    total_concepts = EvaluationConcept.objects.count()
    if total_concepts == 0:
        objeto.rating_schema = 0.0
        objeto.save()
        return

    metadatos_schema = EvaluationMetadata.objects.all()
    for i in MetadataQualificationConcept.objects.all():
        for j in metadatos_schema:
            if (i.evaluation_automatic_evaluation.learning_object.id == objeto.learning_object.id):
                if (i.evaluation_concept == j.evaluation_concept):
                    if (j.schema.find('accessibilityHazard:') >= 0):
                        for k in META.accesibility_hazard.lower().split(','):
                            if (k.replace(' ', '').lower() == j.schema.lower().split(':')[1]):
                                dato = 1
                    if (j.schema.find('accessibilityFeature:') >= 0):
                        if (META.accesibility_features.lower().find(j.schema.lower().split(':')[1]) >= 0):
                            dato = 1
                    if (j.schema.find('accessibilityControl:') >= 0):
                        if (META.accesibility_control.lower().find(j.schema.lower().split(':')[1]) >= 0):
                            dato = 1
                    if (j.schema.find('accessMode:') >= 0):
                        if (META.annotation_modeaccess.lower().find(j.schema.lower().split(':')[1]) >= 0):
                            dato = 1
                    if (j.schema.find('accessModeSufficient:') >= 0):
                        if (META.annotation_modeaccesssufficient.lower().find(j.schema.lower().split(':')[1]) >= 0):
                            dato = 1
                    if (j.schema.find('alignment_types:') >= 0):
                        if (META.classification_purpose.lower().find(j.schema.lower().split(':')[1]) >= 0):
                            dato = 1
                    evaluaction = MetadataSchemaQualification.objects.create(
                        evaluation_metadata=i,
                        evaluation_schema=j,
                        qualification=dato
                    )
                    evaluaction.save()
                    dato = 0
    consult_evaluation = MetadataQualificationConcept.objects.filter(
        evaluation_automatic_evaluation__learning_object__id=objeto.learning_object.id)

    ratingnew = 0
    for i in consult_evaluation:
        vartotal = 0
        cont = 0
        for j in MetadataSchemaQualification.objects.filter(evaluation_metadata=i.id):
            vartotal += j.qualification
            cont += 1
        if cont == 0:
            h = 0.0
        else:
            h = (vartotal * 5) / (1 * cont)
        i.average_schema = h
        i.save()
        ratingnew += h
    objeto.rating_schema = ratingnew / total_concepts

    if (objeto.rating_schema >= 4.0):
        #Cambio de variable, no publicar directamente los OA, deben pasar por revisi?n
        META.public = False
        META.save()
        mail_upload_OA_Satisfy_User.sendMail_Satisfay_User(
            LEARNING_OBJECT_REVIEW_EMAIL,
            LEARNING_OBJECT_REVIEW_NAME,
            META.general_title,
        )
    else:
        user_id = META.user_created_id
        user_te = User.objects.get(pk=user_id)
        user_name_lastname = user_te.first_name + " " + user_te.last_name
        user_email_Te = user_te.email

        mail_upload_OA_Not_Satisfy_User.sendMail_Not_Satisfay_User(user_email_Te, user_name_lastname,
                                                                   META.general_title)
        mail_upload_OA_Not_Satisfy.sendMail_Not_Satisfay_Admin(
            LEARNING_OBJECT_REVIEW_EMAIL,
            LEARNING_OBJECT_REVIEW_NAME,
            META.general_title,
        )

    objeto.save()

def manual_evaluation_metada_learning_object(META):
    """Evalúa metadata no adaptada usando autoevaluaciones por pregunta.

    El umbral heredado para publicar automáticamente en este flujo es menor que
    el del flujo totalmente automático.
    """
    evaluation_concept = EvaluationConcept.objects.all()
    array_concept_evaluation = []
    rating_schema_res = 0

    create_metadata_automatic = None
    for concept in evaluation_concept:
        concept_response = {
            'id': None,
            'qualification_concept': None
        }
        schema_self_questions_concept = MetadataSchemaQuestionQualification.objects.filter(
            learning_object_file_id=META.learning_object_file_id, self_evaluation_question__evaluation_concept=concept.id)
        concept_qualification = 0
        concept_questions = len(schema_self_questions_concept)
        qualification_total = 0
        if concept_questions > 0:
            concept_qualification = 0
            for item in schema_self_questions_concept:
                concept_qualification = concept_qualification + item.qualification
            qualification_total = (5*concept_qualification)/concept_questions
        concept_response['id']=concept.id
        concept_response['qualification_concept'] = round(qualification_total, 2)
        rating_schema_res = rating_schema_res + concept_response['qualification_concept']
        array_concept_evaluation.append(concept_response)

    total_concepts = len(evaluation_concept)
    if total_concepts == 0:
        return

    rating_schema_total = round((rating_schema_res/total_concepts),2)
    if rating_schema_total != 0:
        create_metadata_automatic = MetadataAutomaticEvaluation.objects.create(
            rating_schema=rating_schema_total,
            learning_object_id=META.id
        )
        create_metadata_automatic.save()

    if create_metadata_automatic:
        for concept_res in array_concept_evaluation:
            create_metadata_qualification_concept = MetadataQualificationConcept.objects.create(
                average_schema=concept_res['qualification_concept'],
                evaluation_automatic_evaluation_id=create_metadata_automatic.id,
                evaluation_concept_id=concept_res['id']
            )
            create_metadata_qualification_concept.save()

    if (rating_schema_total >= 2.5):
        #Cambio de variable, no publicar directamente los OA, deben pasar por revisi?n
        META.public = False
        META.save()

        mail_upload_OA_Satisfy.sendMailCreateOA(
            LEARNING_OBJECT_REVIEW_EMAIL,
            LEARNING_OBJECT_REVIEW_NAME,
            META.general_title,
        )
    else:
        user_id = META.user_created_id
        user_te = User.objects.get(pk=user_id)
        user_name_lastname = user_te.first_name + " " + user_te.last_name
        user_email_Te = user_te.email

        mail_upload_OA_Not_Satisfy_User.sendMail_Not_Satisfay_User(user_email_Te, user_name_lastname,META.general_title)

        mail_upload_OA_Not_Satisfy.sendMail_Not_Satisfay_Admin(
            LEARNING_OBJECT_REVIEW_EMAIL,
            LEARNING_OBJECT_REVIEW_NAME,
            META.general_title,
        )

@extend_schema_view(
    get=extend_schema(
        tags=LEARNING_OBJECT_METADATA_TAG,
        summary='Listar los OAs publicos mas recientes',
        description='Devuelve los cuatro objetos de aprendizaje publicos ordenados por fecha de creacion descendente.',
        responses={200: LearningObjectMetadataAllSerializer(many=True)},
    )
)
class learningObjectsTheMostRecent(ListAPIView):
    """Devuelve los cuatro OAs públicos más recientes."""
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataAllSerializer
    def get_queryset(self):
        learning_objects_most_recent = LearningObjectMetadata.objects.filter(public=True).order_by('-created')[:4]
        return learning_objects_most_recent
