import django_filters
from applications.interaction.models import Interaction
from applications.evaluation_collaborating_expert.serializers import QuestionQualificationSearchSerializer
from applications.evaluation_student.models import StudentEvaluation
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert, EvaluationConcept, EvaluationMetadata, EvaluationQuestionsQualification, MetadataAutomaticEvaluation, MetadataQualificationConcept, MetadataSchemaQualification
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from django.db.models import Q
from rest_framework.generics import ListAPIView,RetrieveAPIView, RetrieveUpdateAPIView
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
    LearningObjectMetadataAllSerializer,
    LearningObjectMetadataYears,
    ROANumberPagination,
    ROANumberPaginationPopular,
    TeacherUploadListSerializer,
    )
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser, IsStudentUser, IsTeacherUser
from .models import Commentary, LearningObjectMetadata
# Create your views here.

class SlugView(RetrieveAPIView):
    """
        Obtener un Objeto de Aprendizaje por el slug
    """
    lookup_field = 'slug'
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataAllSerializer
    def get_queryset(self):
        slug = self.kwargs['slug']
        obj = LearningObjectMetadata.objects.learningobjectBySlug(slug)
        return obj

class OAFilter(filters.FilterSet):
    """
        Filtros para OAs no evaluados
    """
    permission_classes = [AllowAny]
    general_title = filters.CharFilter(lookup_expr='icontains')
    education_levels__id = filters.CharFilter(lookup_expr='iexact')
    knowledge_area__id = filters.CharFilter(lookup_expr='iexact')
    license__value = filters.CharFilter(lookup_expr='iexact')
    created__year = filters.CharFilter(lookup_expr='iexact')
    accesibility_control = filters.CharFilter(method='accesibility_control_filter')
    annotation_modeaccess = filters.CharFilter(method='annotation_modeaccess_filter')
    accesibility_features = filters.CharFilter(method='accesibility_features_filter')
    accesibility_hazard = filters.CharFilter(method='accesibility_hazard_filter')

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
            'created__year'
        ]
    def accesibility_control_filter(self, queryset, name, value):
        accesibility_control = self.request.GET.getlist('accesibility_control')
        if len(accesibility_control)==1 and 'fullkeyboardcontrol' in accesibility_control:
            return queryset.filter(
                accesibility_control__icontains =  'fullkeyboardcontrol'
            )
        elif len(accesibility_control)==1 and 'fullMouseControl' in accesibility_control:
            return queryset.filter(
                accesibility_control__icontains =  'fullMouseControl'
            )
        elif len(accesibility_control) == 2 and 'fullMouseControl' in accesibility_control and 'fullkeyboardcontrol' in accesibility_control:
            return queryset.filter(
                Q(accesibility_control__icontains =  'fullkeyboardcontrol') |
                Q(accesibility_control__icontains =  'fullMouseControl')
            
            )
    def annotation_modeaccess_filter(self, queryset, name, value):
        access_preferences = self.request.GET.getlist('annotation_modeaccess') 
        if len(access_preferences)==1 and 'Visual' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'Visual'
            )
        if len(access_preferences)==1 and 'Text' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'Text'
            )
        if len(access_preferences)==1 and 'colorDependent' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'colorDependent'
            )
        if len(access_preferences)==1 and 'Auditory' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'Auditory'
            )
        if len(access_preferences)==2 and 'Visual' in access_preferences and 'Text' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')
            )
        if len(access_preferences)==2 and 'Visual' in access_preferences and 'colorDependent' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'colorDependent')
            )
        if len(access_preferences)==2 and 'Visual' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==2 and 'Text' in access_preferences and 'colorDependent' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')
            )
        if len(access_preferences)==2 and 'Text' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==2 and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==3 and 'Visual' in access_preferences and 'Text' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==3 and 'Visual' in access_preferences and 'Text' in access_preferences and 'colorDependent' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')
            )
        if len(access_preferences)==3 and 'Text' in access_preferences and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==3 and 'Visual' in access_preferences and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==4 and 'Visual' in access_preferences and 'Text' in access_preferences and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
    def accesibility_hazard_filter(self, queryset, name, value):
        hazard_preferences = self.request.GET.getlist('accesibility_hazard') 
        if len(hazard_preferences)==1 and 'noFlashingHazard' in hazard_preferences:
            return queryset.filter(
               accesibility_hazard__icontains =  'noFlashingHazard'
            )
        elif len(hazard_preferences)==1 and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'FlashingHazard')
            )
        elif len(hazard_preferences)==1 and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )
        elif len(hazard_preferences)==2 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'noFlashingHazard')|
               Q(accesibility_hazard__icontains =  'FlashingHazard')
            )
        elif len(hazard_preferences)==2 and 'noFlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'noFlashingHazard')|
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )
        elif len(hazard_preferences)==2 and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'FlashingHazard')|
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )
        elif len(hazard_preferences)==3 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'noFlashingHazard')|
               Q(accesibility_hazard__icontains =  'FlashingHazard')|
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )

    def accesibility_features_filter(self, queryset, name, value):
        access_preferences = self.request.GET.getlist('accesibility_features') 
        if len(access_preferences)==1 and 'captions' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'captions'
            )
        if len(access_preferences)==1 and 'ttsMarkup' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'ttsMarkup'
            )
        if len(access_preferences)==1 and 'audioDescription' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'audioDescription'
            )
        if len(access_preferences)==1 and 'alternativeText' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'alternativeText'
            )
        if len(access_preferences)==2 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')
            )
        if len(access_preferences)==2 and 'captions' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'audioDescription')
            )
        if len(access_preferences)==2 and 'captions' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==2 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')
            )
        if len(access_preferences)==2 and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==2 and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')
            )
        if len(access_preferences)==3 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==3 and 'captions' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==4 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )


class OAFilterExpert(filters.FilterSet):
    """
        Filtros para OAs evaluados
    """
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
        query= queryset.all()
        return query
    def key_preferences_filter(self, queryset, name, value):
        key_preferences = self.request.GET.getlist('key_preferences')
        if len(key_preferences)==1 and 'fullkeyboardcontrol' in key_preferences:
            return queryset.filter(
                accesibility_control__icontains =  'fullkeyboardcontrol'
            )
        elif len(key_preferences)==1 and 'fullMouseControl' in key_preferences:
            return queryset.filter(
                accesibility_control__icontains =  'fullMouseControl'
            )
        elif len(key_preferences) == 2 and 'fullMouseControl' in key_preferences and 'fullkeyboardcontrol' in key_preferences:
            return queryset.filter(
                Q(accesibility_control__icontains =  'fullkeyboardcontrol') |
                Q(accesibility_control__icontains =  'fullMouseControl')
            
            )
    def annotation_modeaccess_filter(self, queryset, name, value):
        access_preferences = self.request.GET.getlist('annotation_modeaccess') 
        if len(access_preferences)==1 and 'Visual' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'Visual'
            )
        if len(access_preferences)==1 and 'Text' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'Text'
            )
        if len(access_preferences)==1 and 'colorDependent' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'colorDependent'
            )
        if len(access_preferences)==1 and 'Auditory' in access_preferences:
            return queryset.filter(
                annotation_modeaccess__icontains =  'Auditory'
            )
        if len(access_preferences)==2 and 'Visual' in access_preferences and 'Text' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')
            )
        if len(access_preferences)==2 and 'Visual' in access_preferences and 'colorDependent' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'colorDependent')
            )
        if len(access_preferences)==2 and 'Visual' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==2 and 'Text' in access_preferences and 'colorDependent' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')
            )
        if len(access_preferences)==2 and 'Text' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==2 and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==3 and 'Visual' in access_preferences and 'Text' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==3 and 'Visual' in access_preferences and 'Text' in access_preferences and 'colorDependent' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')
            )
        if len(access_preferences)==3 and 'Text' in access_preferences and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==3 and 'Visual' in access_preferences and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
        if len(access_preferences)==4 and 'Visual' in access_preferences and 'Text' in access_preferences and 'colorDependent' in access_preferences and 'Auditory' in access_preferences:
            return queryset.filter(
               Q(annotation_modeaccess__icontains =  'Visual')|
               Q(annotation_modeaccess__icontains =  'Text')|
               Q(annotation_modeaccess__icontains =  'colorDependent')|
               Q(annotation_modeaccess__icontains =  'Auditory')
            )
    def accesibility_hazard_filter(self, queryset, name, value):
        hazard_preferences = self.request.GET.getlist('accesibility_hazard') 
        if len(hazard_preferences)==1 and 'noFlashingHazard' in hazard_preferences:
            return queryset.filter(
               accesibility_hazard__icontains =  'noFlashingHazard'
            )
        elif len(hazard_preferences)==1 and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'FlashingHazard')
            )
        elif len(hazard_preferences)==1 and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )
        elif len(hazard_preferences)==2 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'noFlashingHazard')|
               Q(accesibility_hazard__icontains =  'FlashingHazard')
            )
        elif len(hazard_preferences)==2 and 'noFlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'noFlashingHazard')|
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )
        elif len(hazard_preferences)==2 and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'FlashingHazard')|
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )
        elif len(hazard_preferences)==3 and 'noFlashingHazard' in hazard_preferences and 'FlashingHazard' in hazard_preferences and 'nomotionsimulationHazard' in hazard_preferences:
            return queryset.filter(
               Q(accesibility_hazard__icontains =  'noFlashingHazard')|
               Q(accesibility_hazard__icontains =  'FlashingHazard')|
               Q(accesibility_hazard__icontains =  'nomotionsimulationHazard')
            )

    def accesibility_features_filter(self, queryset, name, value):
        access_preferences = self.request.GET.getlist('accesibility_features') 
        if len(access_preferences)==1 and 'captions' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'captions'
            )
        if len(access_preferences)==1 and 'ttsMarkup' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'ttsMarkup'
            )
        if len(access_preferences)==1 and 'audioDescription' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'audioDescription'
            )
        if len(access_preferences)==1 and 'alternativeText' in access_preferences:
            return queryset.filter(
                accesibility_features__icontains =  'alternativeText'
            )
        if len(access_preferences)==2 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')
            )
        if len(access_preferences)==2 and 'captions' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'audioDescription')
            )
        if len(access_preferences)==2 and 'captions' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==2 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')
            )
        if len(access_preferences)==2 and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==2 and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==3 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')
            )
        if len(access_preferences)==3 and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==3 and 'captions' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )
        if len(access_preferences)==4 and 'captions' in access_preferences and 'ttsMarkup' in access_preferences and 'audioDescription' in access_preferences and 'alternativeText' in access_preferences:
            return queryset.filter(
               Q(accesibility_features__icontains =  'captions')|
               Q(accesibility_features__icontains =  'ttsMarkup')|
               Q(accesibility_features__icontains =  'audioDescription')|
               Q(accesibility_features__icontains =  'alternativeText')
            )


class SerachAPIView(ListAPIView):
    """
        Endpoint para el filtro de Objetos de Aprendizaje
    """
    permission_classes = [AllowAny]
    queryset = LearningObjectMetadata.objects.all().exclude(public=False).order_by('id')
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    filter_class = OAFilter

class SerachAPIViewExpert(ListAPIView):
    """
        Buscar todos los Objeto de Aprendizaje evlaudos por el experto
    """
    permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class= ROANumberPagination
    filter_class = OAFilterExpert
    def get_queryset(self):
        is_eval = self.request.GET.get('is_evaluated')
        if is_eval == 'True': 
            query = LearningObjectMetadata.objects.filter(
                learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
            ).exclude(
                public=False
            ).order_by('-id')
            return query
        elif is_eval == 'False':
            query= LearningObjectMetadata.objects.filter(
                public = True
            ).exclude(
                learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
            ).order_by('-id')
            return query
            

class OAEvaluadedFilter(django_filters.FilterSet):
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
        return queryset.filter(
           concept_evaluations__evaluation_collaborating_expert__learning_object__general_title__icontains =  value
        )
    def education_level_filter(self, queryset, name, value):
        return queryset.filter(
           concept_evaluations__evaluation_collaborating_expert__learning_object__education_levels__description__iexact =  value
        )
    def knowledge_area_name_filter(self, queryset, name, value):
        return queryset.filter(
           concept_evaluations__evaluation_collaborating_expert__learning_object__knowledge_area__name__iexact =  value
        )
    def license_description_filter(self, queryset, name, value):
        return queryset.filter(
           concept_evaluations__evaluation_collaborating_expert__learning_object__license__description__iexact =  value
        )
    def created_year_filter(self, queryset, name, value):
        return queryset.filter(
           concept_evaluations__evaluation_collaborating_expert__learning_object__created__year__iexact =  value
        )
    def preferences_description_filter(self, queryset, name, value):
        return queryset.filter(
           evaluation_question__evaluation_concept__concept__iexact =  value
        )


class SerachEvaluatedAPIView(ListAPIView):
    """
        Buscar Objetos de Aprendizaje evaluados
    """
    permission_classes = [AllowAny]
    queryset = EvaluationQuestionsQualification.objects.filter(
        concept_evaluations__evaluation_collaborating_expert__learning_object__public = True,
        ).order_by(
            '-concept_evaluations__evaluation_collaborating_expert__learning_object__id'
        ).distinct('concept_evaluations__evaluation_collaborating_expert__learning_object__id')
    serializer_class = QuestionQualificationSearchSerializer
    pagination_class= ROANumberPagination
    filter_class = OAEvaluadedFilter

class LearningObjectMetadataViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsTeacherUser]
        return [permission() for permission in permission_classes]
    serializer_class = LearningObjectMetadataSerializer
    queryset = LearningObjectMetadata.objects.all()
    
    def perform_create(self, serializer):
        """
            Crear los metadadtos de los OA. API acesible para usurio docentes
        """
        serializer.save(
            user_created=self.request.user
        )
        automaticEvaluation(serializer.data['id'])
        
    def list(self, request):
        """
            Listado de metadatos de los Objetos deaprendizaje. API acesible para todos los usurios
        """
        user = self.request.user
        queryset = LearningObjectMetadata.objects.learning_object_metadata_by_user(user)
        serializer = LearningObjectMetadataAllSerializer(queryset,many=True)
        return Response(serializer.data,status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Listado de metadatos de los Objetos deaprendizaje por id. API acesible para todos los usurios
        """
        user = self.request.user
        queryset = LearningObjectMetadata.objects.learning_object_metadata_retrieve_by_user(user,pk)
        serializer = LearningObjectMetadataAllSerializer(queryset)
        return Response(serializer.data,status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        """
            Actualizar los metadadtos de los OA. API acesible para usurio docentes
        """
        user = self.request.user
        LearningObjectMetadata.objects.learning_object_metadata_by_user_destroy(user,pk)
        return Response({"message": "success"},status=HTTP_200_OK)

class ListLearningObjectPublicAndPrivate(ListAPIView):
    """
        Listar Objetos de Aprendizaje publicos y privados
    """
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    lookup_field = "public"
    def get_queryset(self):
        filter = self.kwargs['public']
        return LearningObjectMetadata.objects.filter(public=filter).order_by('-pk')


class UpdatePublicLearningObject(RetrieveUpdateAPIView):
    """
        Actualizar estado de un OA
    """
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    serializer_class = LearningObjectMetadataAllSerializer
    queryset = LearningObjectMetadata.objects.all()


class TotalLearningObjectAproved(APIView):
    """
        Obtener el total de los Objetos de Aprendizaje aprobados y por aprobar
    """
    permission_classes = [AllowAny]
    def get(self, request, format=None):
        learning_approved= LearningObjectMetadata.objects.filter(
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

class ListLearningObjectPopular(ListAPIView):
    """
        Listar los Objetos de Aprendizaje más valorados.
    """
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataPopularSerializer
    pagination_class = None
    # pagination_class = ROANumberPaginationPopular
    def get_queryset(self):
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__public=True,rating__gte = 1.3
        ).order_by('-learning_object__id','-rating').distinct('learning_object__id')[:8]
        return query

class ListLearningObjectEvaluatedByExpert(ListAPIView):
    """
        Listar los Objetos de Aprendizaje evaluados por un experto con el id del experto
    """
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    serializer_class = LearningObjectMetadataByExpet
    pagination_class = ROANumberPagination
    def get_queryset(self):
        id = self.kwargs['id']
        query = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=id
        ).order_by('-id')
        return query

class ListLearningObjectEvaluatedByStudent(ListAPIView):
    """
        Listar los Objetos de Aprendizaje evaluados por un estudiante con el id del estudiante
    """
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    serializer_class = LearningObjectMetadataByStudent
    pagination_class = ROANumberPagination
    def get_queryset(self):
        id = self.kwargs['id']
        query = StudentEvaluation.objects.filter(
            student__student__id=id
        ).order_by('-id')
        return query

class ListLearningObjectUploadByTeacher(ListAPIView):
    """
        Listar los Objetos de Aprendizaje cargados por un docente.
    """
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    def get_queryset(self):
        id = self.kwargs['id']
        query = LearningObjectMetadata.objects.filter(
            user_created__teacher__id=id
        ).order_by('-id')
        return query

class ListLearningObjecYears(ListAPIView):
    """
        Listar los años de publicación de los Objeto de aprendizaje
    """
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataYears
    pagination_class = None
    def get_queryset(self):
        query = LearningObjectMetadata.objects.filter(
            public=True
        ).distinct('created__year')
        return query

class CommentaryModelView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, Or(IsTeacherUser,IsStudentUser,IsCollaboratingExpertUser)]
    serializer_class = CommentarySerializer
    queryset = Commentary.objects.all()
    def perform_create(self, serializer):
        """
            Crear un comentarion
        """
        serializer.save(
            user=self.request.user
        )
    def retrieve(self, request, pk=None):
        """
            Obtener Cometario por Id
        """
        queryset = Commentary.objects.filter(
            user__id=self.request.user.id
        )
        comment = get_object_or_404(queryset, pk=pk)
        serializer = CommentarySerializer(comment)
        return Response(serializer.data, status=HTTP_200_OK)
    def list(self, request):
        """
            Listado de todos comentarios del usurios que lo realizo
        """
        queryset = Commentary.objects.filter(
            user__id=self.request.user.id
        )
        serializer = CommentarySerializer(queryset,many=True)
        return Response(serializer.data,status=HTTP_200_OK)

class CommentaryListAPIView(ListAPIView):
    """
        Listar los comentarios correspondiente a un Objeto de aprendizaje
    """
    permission_classes = [AllowAny]
    serializer_class = CommentaryListSerializer
    pagination_class = ROANumberPaginationPopular
    def get_queryset(self):
        id = self.kwargs['pk']
        return Commentary.objects.filter(
            learning_object__id=id
        )
class LearningObjectMetadataViewedAPIView(ListAPIView):
    """
        Listar Objetos de aprendizaje evaluados por un experto
    """
    permission_classes = [IsAuthenticated, (IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser)]
    serializer_class = LearningObjectMetadataPopularSerializer
    pagination_class = ROANumberPaginationPopular
    def get_queryset(self):
        query = list(Interaction.objects.filter(user = self.request.user))
        oa_list_viewed = []
        for q in query:
            oa_list_viewed.append(q.learning_object.id)
        queryset = EvaluationCollaboratingExpert.objects.filter(
                learning_object__id__in = oa_list_viewed
        ).order_by('-learning_object__id').distinct('learning_object__id')
        return queryset

class LearningObjectTecherListAPIView(ListAPIView):
    """
        Listar Objetos de aprendizaje cargados por un docente
    """
    permission_classes = [IsAuthenticated, (IsTeacherUser | IsStudentUser | IsCollaboratingExpertUser)]
    serializer_class = TeacherUploadListSerializer
    pagination_class = ROANumberPaginationPopular
    def get_queryset(self):
        queryset = LearningObjectMetadata.objects.filter(
                user_created = self.request.user
        ).order_by('-created')
        return queryset



#########METODO PARA CALIFICAR UN OAS automaticamente 
def automaticEvaluation(id):
    META=LearningObjectMetadata.objects.get(id=id)
    objeto=MetadataAutomaticEvaluation.objects.create(
        learning_object=META,
        rating_schema=0.0
    )
    objeto.save()
    for i in EvaluationConcept.objects.all():
        concept=MetadataQualificationConcept.objects.create(
            evaluation_concept=i,
            evaluation_automatic_evaluation=objeto,
            average_schema=0.0
        )
        concept.save()
    
    dato=0
    metadatos_schema=EvaluationMetadata.objects.all()
    for i in MetadataQualificationConcept.objects.all():
        for j in metadatos_schema:
            if (i.evaluation_automatic_evaluation.learning_object.id==objeto.learning_object.id):
                
                if (i.evaluation_concept == j.evaluation_concept):
                    if(j.schema.find('accessibilityHazard:')>=0):
                        for k in META.accesibility_hazard.lower().split(','):
                            if (k.replace(' ','')==j.schema.lower().split(':')[1]):
                                dato=1
                    if(j.schema.find('accessibilityFeature:')>=0):
                        if(META.accesibility_features.lower().find(j.schema.lower().split(':')[1])>=0):
                            dato=1
                    if(j.schema.find('accessibilityControl:')>=0):
                        if(META.accesibility_control.lower().find(j.schema.lower().split(':')[1])>=0):
                            dato=1
                    if(j.schema.find('accessMode:')>=0):
                        if(META.annotation_modeaccess.lower().find(j.schema.lower().split(':')[1])>=0):
                            dato=1
                    if(j.schema.find('accessModeSufficient:')>=0):
                        if(META.annotation_modeaccesssufficient.lower().find(j.schema.lower().split(':')[1])>=0):
                            dato=1 
                    evaluaction=MetadataSchemaQualification.objects.create(
                    evaluation_metadata=i,
                    evaluation_schema=j,
                    qualification=dato
                    )
                    evaluaction.save()
                    dato=0
    

    consult_evaluation=MetadataQualificationConcept.objects.filter(evaluation_automatic_evaluation__learning_object__id=objeto.learning_object.id)
    
    ratingnew=0
    for i in consult_evaluation:
        vartotal=0
        cont=0
        for j in MetadataSchemaQualification.objects.filter(evaluation_metadata=i.id):
            vartotal+=j.qualification
            cont+=1
        h=(vartotal*5)/(1*cont)
        i.average_schema=h
        i.save()
        ratingnew+=h
    objeto.rating_schema=ratingnew/len(EvaluationConcept.objects.all())
    objeto.save()


    
