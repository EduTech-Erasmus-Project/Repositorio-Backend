"""Vistas para administrar y ejecutar la evaluación colaborativa experta.

Este módulo concentra varios flujos relacionados:

- CRUD administrativo de conceptos, preguntas y esquemas
- captura de evaluaciones expertas sobre objetos de aprendizaje
- consultas públicas y privadas de resultados
- soporte para evaluación automática de metadata y auto-preguntas
"""

from django.shortcuts import render
from django.db import transaction
from django.db.models.signals import post_save
from yaml import serialize

from applications.learning_object_metadata.serializers import LearningObjectMetadataAllSerializer, \
    LearningObjectMetadataByExpet, ROANumberPagination
from applications.learning_object_metadata.models import LearningObjectMetadata
from rest_framework import viewsets
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser ,IsTeacherUser
from applications.user.models import User
from applications.evaluation_collaborating_expert.serializers import (
    EvaluationAutomaticEvaluationSerializer,
    EvaluationCollaboratingExpertEvaluationSerializer,
    EvaluationCollaboratingExpertSerializer,
    EvaluationConceptListSerializer,
    EvaluationConceptListSerializerSCHEMA,
    EvaluationConceptSerializer,
    EvaluationExpertCreateSerializer,
    EvaluationMetadataRegisterSerializer,
    EvaluationMetadataSerializer,
    EvaluationQuestionRegisterSerializer,
    EvaluationQuestionSerializer,
    EvaluationQuestionQualificationSerializer,
    QuestionQualificationListSerializer,
    EvaluationSelfQuestionListSerializerSCHEMA,
    EvaluationSelfQuestionSerializer,
    RelationshipQuestionAndMetadata
)
from .models import (
    EvaluationConcept,
    EvaluationMetadata,
    EvaluationQuestion,
    EvaluationQuestionsQualification,
    EvaluationConceptQualification,
    EvaluationCollaboratingExpert,
    MetadataAutomaticEvaluation,
    MetadataQualificationConcept,
    SelfEvaluationQuestions,
    MetadataSchemaQuestionQualification
)
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework.response import Response
from rest_framework import serializers
from roabackend.settings import NO, PARTIALLY, YES, CALIFICATION_OPTIONS, NOT_APPLY


EVALUATION_EXPERT_TAG = ['Evaluation Collaborating Expert']
EVALUATION_EXPERT_RUBRIC_TAG = ['Evaluation Expert Rubric']
EVALUATION_EXPERT_RESULTS_TAG = ['Evaluation Expert Results']
EVALUATION_EXPERT_ADMIN_TAG = ['Evaluation Expert Admin']
EVALUATION_EXPERT_METADATA_TAG = ['Evaluation Expert Metadata']

EXPERT_EVALUATION_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador interno usado por la ruta. Segun el endpoint puede representar una evaluacion, pregunta, concepto, schema u OA.',
)
EXPERT_EVALUATION_OA_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador del objeto de aprendizaje consultado.',
)
EXPERT_EVALUATION_PK_PARAMETER = OpenApiParameter(
    'pk',
    int,
    OpenApiParameter.PATH,
    description='Identificador interno del recurso recibido en la ruta legacy.',
)

MessageResponseSerializer = inline_serializer(
    name='EvaluationCollaboratingExpertMessage',
    fields={
        'message': serializers.CharField(),
        'code': serializers.IntegerField(required=False),
        'data': serializers.JSONField(required=False),
    },
)
EvaluationExpertEmptyResponseSerializer = inline_serializer(
    name='EvaluationCollaboratingExpertEmptyResponse',
    fields={
        'detail': serializers.CharField(required=False),
    },
)

class MetadataSelfQuestionAnswerSerializer(serializers.Serializer):
    idQuestion = serializers.IntegerField()
    answer = serializers.CharField()


class MetadataSelfQuestionRequestSerializer(serializers.Serializer):
    learning_object_id = serializers.IntegerField()
    answerQuestion = MetadataSelfQuestionAnswerSerializer(many=True)


@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_EXPERT_RUBRIC_TAG,
        summary='Listar conceptos de evaluacion experta',
        description='Lista las dimensiones principales de la rubrica experta junto con sus preguntas asociadas.',
        responses={200: EvaluationConceptListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_EXPERT_RUBRIC_TAG,
        summary='Consultar concepto de evaluacion experta',
        description=(
            'Endpoint heredado generado por el router. La implementacion actual no recupera correctamente el concepto; '
            'para detalle estructurado se recomienda usar el listado de conceptos o el endpoint de schemas.'
        ),
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationConceptListSerializer, 404: OpenApiResponse(description='Concepto no encontrado.')},
    ),
    create=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Crear concepto de evaluacion experta',
        description='Crea una dimension principal de la rubrica experta. Requiere administrador.',
        request=EvaluationConceptSerializer,
        responses={201: EvaluationConceptSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar concepto de evaluacion experta',
        description='Actualiza el texto del concepto de evaluacion indicado.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationConceptSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar parcialmente concepto de evaluacion experta',
        description='Operacion generada por router. Se recomienda usar PUT porque el metodo custom espera el campo `concept`.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationConceptSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Eliminar concepto de evaluacion experta',
        description='Elimina un concepto de la rubrica experta por identificador.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: MessageResponseSerializer, 404: OpenApiResponse(description='Concepto no encontrado.')},
    ),
)
class EvaluationConceptViewSet(viewsets.ModelViewSet):
    """CRUD administrativo de conceptos de evaluación para OAs.

    `list` queda abierto para lectura, mientras que crear, editar y eliminar
    se reservan a administración.
    """

    def get_permissions(self):
        if (self.action == 'list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = EvaluationConceptSerializer
    queryset = EvaluationConcept.objects.all()
    action_serializers = {
        'list': EvaluationConceptListSerializer,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationConceptViewSet, self).get_serializer_class()

    @transaction.atomic
    def update(self, request, pk=None, project_pk=None):
        """Actualiza el texto del concepto de evaluacion."""
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.concept = request.data['concept']
        instance.save()
        return Response({"message": "success"}, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera un concepto de evaluación por su identificador."""
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationConceptListSerializer(instance)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """Elimina un concepto de evaluación por identificador."""
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"}, status=HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_EXPERT_RUBRIC_TAG,
        summary='Listar preguntas de evaluacion experta',
        description='Lista preguntas de la rubrica experta con metadata, codigo, interpretes de respuesta, peso y relevancia.',
        responses={200: EvaluationQuestionSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_EXPERT_RUBRIC_TAG,
        summary='Consultar pregunta de evaluacion experta',
        description='Recupera una pregunta experta por identificador.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationQuestionSerializer, 404: OpenApiResponse(description='Pregunta no encontrada.')},
    ),
    create=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Crear pregunta de evaluacion experta',
        description='Crea una pregunta experta asociada a un concepto, con interpretes, peso, relevancia y codigo unico.',
        request=EvaluationQuestionSerializer,
        responses={201: EvaluationQuestionSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar pregunta de evaluacion experta',
        description='Actualiza una pregunta experta y sus campos de interpretacion, peso, relevancia, schema y codigo.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationQuestionRegisterSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar parcialmente pregunta de evaluacion experta',
        description='Operacion generada por router. Se recomienda usar PUT porque el metodo custom espera el payload completo.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationQuestionRegisterSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Eliminar pregunta de evaluacion experta',
        description='Elimina una pregunta experta por identificador.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: MessageResponseSerializer, 404: OpenApiResponse(description='Pregunta no encontrada.')},
    ),
)
class EvaluationQuestionsViewSet(viewsets.ModelViewSet):
    """CRUD administrativo de preguntas expertas y su configuración de pesos."""

    def get_permissions(self):
        if (self.action == 'list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = EvaluationQuestionSerializer
    queryset = EvaluationQuestion.objects.all()

    def update(self, request, pk=None, project_pk=None):
        """Actualiza una pregunta experta y sus interpretes asociados."""

        queryset = EvaluationQuestion.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationQuestionRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.question = serializer.validated_data['question']
        instance.description = serializer.validated_data['description']
        instance.schema = serializer.validated_data['schema']
        instance.code = serializer.validated_data['code']
        instance.interpreter_yes = serializer.validated_data['interpreter_yes']
        instance.interpreter_no = serializer.validated_data['interpreter_no']
        instance.interpreter_partially = serializer.validated_data['interpreter_partially']
        instance.interpreter_not_apply = serializer.validated_data['interpreter_not_apply']
        instance.value_importance = serializer.validated_data['value_importance']
        instance.weight = serializer.validated_data['weight']
        instance.relevance = serializer.validated_data['relevance']
        instance.save()
        return Response({"message": "success"}, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera una pregunta experta por identificador."""
        queryset = EvaluationQuestion.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationQuestionSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """Elimina una pregunta experta por identificador."""
        queryset = EvaluationQuestion.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"}, status=HTTP_200_OK)


class EvaluationQuestionsQualificationVieeSet(viewsets.ModelViewSet):
    """CRUD de calificaciones por pregunta dentro de una evaluación experta."""

    def get_permissions(self):
        if (self.action == 'create' or self.action == 'list' or self.action == 'retrieve'):
            permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
        else:
            permission_classes = [IsAuthenticated, IsCollaboratingExpertUser, IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = EvaluationQuestionQualificationSerializer
    queryset = EvaluationQuestionsQualification.objects.all()
    action_serializers = {
        'list': QuestionQualificationListSerializer,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationConceptViewSet, self).get_serializer_class()

    def perform_create(self, serializer):
        """Mantiene el hook de creación heredado del ViewSet."""
        serializer.save(
            user_created=self.request.user
        )


@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Listar evaluaciones del experto autenticado',
        description='Lista las evaluaciones creadas por el experto colaborador autenticado.',
        responses={200: EvaluationCollaboratingExpertSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Obtener evaluacion experta',
        description='Recupera una evaluacion concreta siempre que pertenezca al experto autenticado.',
        parameters=[
            EXPERT_EVALUATION_ID_PARAMETER,
        ],
        responses={
            200: EvaluationCollaboratingExpertSerializer,
            404: OpenApiResponse(description='Evaluacion no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Registrar evaluacion experta',
        description=(
            'Registra la evaluacion de un experto sobre un OA. El payload envia el id del OA, observacion y respuestas '
            'por pregunta. La vista crea promedios por concepto, calcula el rating final y marca como prioritaria la primera evaluacion disponible.'
        ),
        request=EvaluationExpertCreateSerializer,
        responses={
            200: EvaluationCollaboratingExpertSerializer,
            400: OpenApiResponse(response=MessageResponseSerializer, description='Payload invalido o OA ya evaluado.'),
        },
    ),
    update=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Actualizar evaluacion experta',
        description='Actualiza respuestas y observacion de una evaluacion experta, recalculando promedios por concepto y rating final.',
        request=EvaluationExpertCreateSerializer,
        parameters=[
            EXPERT_EVALUATION_ID_PARAMETER,
        ],
        responses={
            200: EvaluationCollaboratingExpertSerializer,
            404: OpenApiResponse(description='Evaluacion no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Eliminar evaluacion experta',
        description='Elimina la evaluacion del experto autenticado junto con sus conceptos y preguntas calificadas.',
        parameters=[
            EXPERT_EVALUATION_ID_PARAMETER,
        ],
        responses={200: MessageResponseSerializer},
    ),
)
class EvaluationCollaboratingExpertView(viewsets.ViewSet):
    """Gestiona el ciclo principal de evaluación experta sobre un OA.

    Crea la cabecera de evaluacion, registra respuestas por pregunta,
    recalcula promedios por concepto y mantiene el rating agregado que luego
    consumen los listados públicos  y privados del modulo.
    """
    serializer_class = EvaluationCollaboratingExpertSerializer

    def get_permissions(self):
        if (self.action == 'create'):
            permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
        else:
            permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
        return [permission() for permission in permission_classes]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Crea una evaluación experta completa para un OA.

        Valida la carga, impide que el mismo experto evalue dos veces el mismo
        objeto y persiste tanto la cabecera de evaluación como los promedios
        por concepto y las calificaciones por pregunta.
        """

        serializer = EvaluationExpertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation_questions_ = []
        qualifications = []
        for result in serializer.validated_data['results']:
            evaluation_questions_.append(result['id'])
            qualifications.append(result['value'])

        user = User.objects.get(id=self.request.user.id)
        oa_is_evaluated = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=serializer.validated_data['learning_object'],
            collaborating_expert__id=user.id
        )

        if oa_is_evaluated:
            return Response({"message": "Learning Object is already evaluated by this expert"},
                            status=HTTP_400_BAD_REQUEST)

        learningObjectMetadata = LearningObjectMetadata.objects.get(
            id=serializer.validated_data['learning_object']
        )

        evaluation_questions = EvaluationQuestion.objects.filter(
            id__in=evaluation_questions_
        )

        evaluation_concept_list = []
        for evaluation_question in evaluation_questions:
            evaluation_concept_list.append(evaluation_question.evaluation_concept.id)

        evaluation_concept_list = list(dict.fromkeys(evaluation_concept_list))
        evaluation_concepts = EvaluationConcept.objects.filter(
            id__in=evaluation_concept_list
        )
        existe_priority = self.filter_is_priority_exits()
        evaluationCollaboratingExpert = None
        if existe_priority is True:
            evaluationCollaboratingExpert = EvaluationCollaboratingExpert.objects.create(
                learning_object=learningObjectMetadata,
                rating=0.0,
                observation=serializer.validated_data['observation'],
                collaborating_expert=user,
            )
        else:
            evaluationCollaboratingExpert = EvaluationCollaboratingExpert.objects.create(
                learning_object=learningObjectMetadata,
                rating=0.0,
                observation=serializer.validated_data['observation'],
                collaborating_expert=user,
                is_priority=True
            )

        ratings = 0.0
        evaluationConceptQualificationList = []
        for evaluation_concept in evaluation_concepts:
            evaluationConceptQualification = EvaluationConceptQualification.objects.create(
                evaluation_concept=evaluation_concept,
                evaluation_collaborating_expert=evaluationCollaboratingExpert,
                average=0.0
            )
            evaluationConceptQualificationList.append(evaluationConceptQualification)

        evaluationQuestionsQualificationList = []
        cont_not_apply = 0
        ref_total_calificaciones = 0
        results_evaluation = serializer.validated_data['results']
        for evaluation_question in evaluation_questions:
            qualification = self.create_evaluation_order_qualification(
                evaluation_question.id,
                results_evaluation,
            )
            for evaluationConceptQualification in evaluationConceptQualificationList:
                if (evaluationConceptQualification.evaluation_concept_id == evaluation_question.evaluation_concept_id):
                    evaluationQuestionsQualification = EvaluationQuestionsQualification.objects.create(
                        concept_evaluations=evaluationConceptQualification,
                        evaluation_question=evaluation_question,
                        qualification=qualification
                    )
                    if not _is_not_apply(qualification):
                        multiplicacion = float(qualification) * float(evaluation_question.weight or 0.0)
                        ratings = ratings + multiplicacion
                        ref_total_calificaciones = ref_total_calificaciones + (2 * float(evaluation_question.weight or 0.0))
                        cont_not_apply += 1
                    evaluationQuestionsQualificationList.append(evaluationQuestionsQualification)

        updateAverage(evaluationQuestionsQualificationList, evaluationConceptQualificationList)
        evaluationCollaboratingExpert.rating = _calculate_normalized_rating(
            ratings,
            ref_total_calificaciones,
            cont_not_apply,
        )

        evaluationCollaboratingExpert.save()

        serializer = EvaluationCollaboratingExpertSerializer(evaluationCollaboratingExpert)
        return Response(serializer.data, status=HTTP_200_OK)


    def create_evaluation_order_qualification(self, id_question, request_data_qualifications):
        """Convierte la respuesta textual del request al puntaje numérico usado internamente."""
        for qualification_reslut in request_data_qualifications:
            if id_question == qualification_reslut['id']:
                if (qualification_reslut['value'] == CALIFICATION_OPTIONS['YES']):
                    return YES
                elif (qualification_reslut['value'] == CALIFICATION_OPTIONS['NO']):
                    return NO
                elif (qualification_reslut['value'] == CALIFICATION_OPTIONS['NOT_APPLY']):
                    return NOT_APPLY
                else:
                    return PARTIALLY

    def filter_is_priority_exits(self):
        """Indica si ya existe una evaluación marcada como prioritaria."""
        collaborating_expert = EvaluationCollaboratingExpert.objects.filter(is_priority=True)
        if len(collaborating_expert) > 0:
            return True
        return False

    def list(self, request):
        """Lista las evaluaciones creadas por el experto autenticado."""
        queryset = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        )
        serializer = EvaluationCollaboratingExpertSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera una evaluación concreta del experto autenticado."""
        queryset = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id,
            id=pk
        )

        get_evaluation_expert = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationCollaboratingExpertSerializer(get_evaluation_expert)

        return Response(serializer.data, status=HTTP_200_OK)

    @transaction.atomic
    def update(self, request, pk=None, project_pk=None):
        """Actualiza respuestas, observación y rating de una evaluación existente."""
        serializer = EvaluationExpertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        )

        evaluation_expert = get_object_or_404(queryset, pk=pk)
        evaluation_expert.observation = serializer.validated_data['observation']

        evaluationQuestionsQualifications = EvaluationQuestionsQualification.objects.filter(
            concept_evaluations__evaluation_collaborating_expert__id=pk
        )

        evaluationConceptQualificationList = list(
            EvaluationConceptQualification.objects.filter(
                evaluation_collaborating_expert__id=pk
            )
        )

        rating = 0.0
        cont_not_apply = 0
        ref_total_calificaciones = 0

        for evaluationQuestionsQualification in evaluationQuestionsQualifications:
            qualification = self.return_qualification_question(
                evaluationQuestionsQualification.evaluation_question_id,
                serializer.validated_data['results'],
            )
            evaluationQuestionsQualification.qualification = qualification
            if not _is_not_apply(qualification):
                wieght_question = float(evaluationQuestionsQualification.evaluation_question.weight or 0.0)
                multiplicacion = float(qualification) * wieght_question
                ref_total_calificaciones = ref_total_calificaciones + (2 * wieght_question)
                rating = rating + multiplicacion
                cont_not_apply += 1

        evaluation_expert.rating = _calculate_normalized_rating(
            rating,
            ref_total_calificaciones,
            cont_not_apply,
        )
        evaluation_expert.save()

        updateAverage(evaluationQuestionsQualifications, evaluationConceptQualificationList)

        EvaluationQuestionsQualification.objects.bulk_update(evaluationQuestionsQualifications, ['qualification'])

        serializer = EvaluationCollaboratingExpertSerializer(evaluation_expert)
        return Response(serializer.data, status=HTTP_200_OK)

    def return_qualification_question(self, id_evaluations, array_qualifications):
        """Busca la respuesta de una pregunta y la convierte al puntaje persistido."""
        for value in array_qualifications:
            if (value['id'] == id_evaluations):
                if (value['value'] == CALIFICATION_OPTIONS['YES']):
                    return YES
                elif (value['value'] == CALIFICATION_OPTIONS['NO']):
                    return NO
                elif (value['value'] == CALIFICATION_OPTIONS['NOT_APPLY']):
                    return NOT_APPLY
                else:
                    return PARTIALLY
        return 0

    @transaction.atomic
    def destroy(self, request, pk=None):
        """Elimina una evaluación experta y sus registros derivados."""
        evaluationQuestionsQualifications = EvaluationQuestionsQualification.objects.filter(
            concept_evaluations__evaluation_collaborating_expert__id=pk
        )
        for evaluationQuestionsQualification in evaluationQuestionsQualifications:
            evaluationQuestionsQualification.delete()

        evaluationConceptQualifications = EvaluationConceptQualification.objects.filter(
            evaluation_collaborating_expert__id=pk
        )
        for evaluationConceptQualification in evaluationConceptQualifications:
            evaluationConceptQualification.delete()

        queryset = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        )
        evaluation_expert = get_object_or_404(queryset, pk=pk)
        evaluation_expert.delete()
        return Response({"message": "success"}, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RUBRIC_TAG,
        summary='Listar rubrica completa para evaluacion experta',
        description=(
            'Entrega la estructura que responde el experto colaborador. La respuesta esta organizada por conceptos '
            'y cada concepto incluye sus preguntas, interpretes de respuesta, peso y relevancia.'
        ),
        responses={
            200: EvaluationConceptListSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol experto colaborador.'),
        },
    )
)
class EvaluationQuestionsExpertView(ListAPIView):
    """Lista los conceptos que estructuran el formulario de evaluación experta."""
    permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
    serializer_class = EvaluationConceptListSerializer

    def get_queryset(self):
        return EvaluationConcept.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RESULTS_TAG,
        summary='Listar OAs ya evaluados por el experto',
        description='Devuelve las evaluaciones realizadas por el experto autenticado, ordenadas desde la mas reciente.',
        responses={
            200: LearningObjectMetadataByExpet(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol experto colaborador.'),
        },
    )
)
class LerningObjectRated(ListAPIView):
    """Lista los OAs que el experto autenticado ya evaluo."""
    permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
    serializer_class = LearningObjectMetadataByExpet
    pagination_class = ROANumberPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EvaluationCollaboratingExpert.objects.none()

        query = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RESULTS_TAG,
        summary='Listar OAs pendientes de evaluar por el experto',
        description='Lista OAs publicos que aun no tienen evaluacion del experto autenticado.',
        responses={
            200: LearningObjectMetadataAllSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol experto colaborador.'),
        },
    )
)
class LerningObjectNotRated(ListAPIView):
    """Lista OAs públicos que todavía no han sido evaluados por el experto actual."""
    permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return LearningObjectMetadata.objects.none()

        query = LearningObjectMetadata.objects.filter(
            public=True
        ).exclude(
            learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RESULTS_TAG,
        summary='Listar evaluaciones expertas publicas de un OA',
        description='Expone publicamente las evaluaciones expertas registradas para el OA indicado.',
        parameters=[EXPERT_EVALUATION_OA_ID_PARAMETER],
        responses={200: EvaluationCollaboratingExpertEvaluationSerializer(many=True)},
    )
)
class ListOAEvaluatedRetriveAPIView(ListAPIView):
    """Expone las evaluaciones registradas para un OA sin requerir autenticación."""
    permission_classes = [AllowAny]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EvaluationCollaboratingExpert.objects.none()

        id = self.kwargs['pk']
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=id,
        ).distinct('learning_object')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RESULTS_TAG,
        summary='Consultar evaluacion experta prioritaria de un OA',
        description=(
            'Devuelve la evaluacion marcada como prioritaria para el OA. Si no existe prioridad, usa una evaluacion del OA como fallback.'
        ),
        parameters=[EXPERT_EVALUATION_OA_ID_PARAMETER],
        responses={200: EvaluationCollaboratingExpertEvaluationSerializer(many=True)},
    )
)
class ListOAEvaluatedPriorityRetriveAPIView(ListAPIView):
    """Devuelve primero la evaluación prioritaria del OA y usa fallback si no existe."""
    permission_classes = [AllowAny]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EvaluationCollaboratingExpert.objects.none()

        id = self.kwargs['pk']
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=id,
            is_priority=True
        )
        if len(query) == 0:
            query = EvaluationCollaboratingExpert.objects.filter(
                learning_object__id=id,
            ).distinct('learning_object')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RESULTS_TAG,
        summary='Listar evaluacion experta principal de un OA',
        description='Ruta heredada para obtener una evaluacion principal asociada al OA indicado.',
        parameters=[EXPERT_EVALUATION_OA_ID_PARAMETER],
        responses={200: EvaluationCollaboratingExpertEvaluationSerializer(many=True)},
    )
)
class ListOAEvaluatedPrincipalRetriveAPIView(ListAPIView):
    """Lista la evaluación principal asociada a un OA para consumo público."""
    permission_classes = [AllowAny]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EvaluationCollaboratingExpert.objects.none()

        id = self.kwargs['pk']
        query = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=id,
        ).distinct('learning_object')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RESULTS_TAG,
        summary='Consultar evaluacion experta del usuario actual para un OA',
        description=(
            'Devuelve la evaluacion experta del usuario actual sobre el OA indicado. '
            'La ruta es publica por compatibilidad, pero solo devolvera resultados si hay usuario autenticado asociado.'
        ),
        parameters=[EXPERT_EVALUATION_OA_ID_PARAMETER],
        responses={200: EvaluationCollaboratingExpertEvaluationSerializer(many=True)},
    )
)
class ListOAEvaluatedRetriveAPIViewSingleUser(ListAPIView):
    """Lista la evaluación del usuario autenticado para un OA concreto."""
    permission_classes = [AllowAny]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EvaluationCollaboratingExpert.objects.none()

        id = self.kwargs['pk']
        return EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=id,
            collaborating_expert__id=self.request.user.id,
        ).distinct('learning_object')


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_RESULTS_TAG,
        summary='Consultar mi evaluacion experta de un OA',
        description='Devuelve la evaluacion registrada por el experto autenticado para el OA indicado.',
        parameters=[EXPERT_EVALUATION_OA_ID_PARAMETER],
        responses={
            200: EvaluationCollaboratingExpertEvaluationSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol experto colaborador.'),
        },
    )
)
class ListOAEvaluatedToExpertRetriveAPIView(ListAPIView):
    """Lista, para el experto autenticado, su propia evaluación de un OA."""

    permission_classes = [IsAuthenticated, IsCollaboratingExpertUser]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EvaluationCollaboratingExpert.objects.none()

        id = self.kwargs['pk']
        return EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__id=self.request.user.id,
            learning_object__id=id,
        ).distinct('learning_object')


def updateAverage(scoreData: list, instances: list):
    """Recalcula el promedio normalizado de cada concepto evaluado.

    Parte de las respuestas por pregunta, aplica los pesos configurados y
    omite respuestas marcadas como `NOT_APPLY` antes de actualizar en lote los
    registros de `EvaluationConceptQualification`.
    """
    concept_stats = {
        instance.evaluation_concept_id: {
            'score': 0.0,
            'reference': 0.0,
            'count': 0,
        }
        for instance in instances
    }
    weight_by_question = {
        question.id: float(question.weight or 0.0)
        for question in EvaluationQuestion.objects.filter(
            id__in=[score.evaluation_question_id for score in scoreData]
        )
    }

    for score in scoreData:
        concept_id = score.concept_evaluations.evaluation_concept_id
        if concept_id not in concept_stats or _is_not_apply(score.qualification):
            continue
        weight_question = weight_by_question.get(score.evaluation_question_id, 0.0)
        concept_stats[concept_id]['score'] += float(score.qualification) * weight_question
        concept_stats[concept_id]['reference'] += 2 * weight_question
        concept_stats[concept_id]['count'] += 1

    for instance in instances:
        stats = concept_stats.get(instance.evaluation_concept_id, {})
        instance.average = _calculate_normalized_rating(
            stats.get('score', 0.0),
            stats.get('reference', 0.0),
            stats.get('count', 0),
        )

    if instances:
        EvaluationConceptQualification.objects.bulk_update(instances, ['average'])


def _is_not_apply(value):
    """Indica si la respuesta recibida corresponde al valor especial `NOT_APPLY`."""
    return float(value) == float(NOT_APPLY)


def _calculate_normalized_rating(score, total_reference, applicable_count):
    """Normaliza el puntaje acumulado a la escala histórica usada por el proyecto."""
    if applicable_count == 0 or total_reference == 0:
        return 0.0

    preliminary_value = round((total_reference / applicable_count), 2) / 5
    if preliminary_value == 0:
        return 0.0

    return round((score / applicable_count) / preliminary_value, 2)

@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_EXPERT_METADATA_TAG,
        summary='Listar conceptos con schemas de metadata',
        description='Lista conceptos de evaluacion junto con los schemas de metadata asociados a cada concepto.',
        responses={200: EvaluationConceptListSerializerSCHEMA(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_EXPERT_METADATA_TAG,
        summary='Consultar concepto con schemas de metadata',
        description='Recupera un concepto concreto con sus schemas de metadata asociados.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationConceptListSerializerSCHEMA, 404: OpenApiResponse(description='Concepto no encontrado.')},
    ),
    create=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Crear concepto para schemas de metadata',
        description='Operacion heredada del ModelViewSet para crear conceptos desde el bloque de schemas.',
        request=EvaluationConceptSerializer,
        responses={201: EvaluationConceptSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar concepto de schema de metadata',
        description='Actualiza el nombre del concepto que agrupa schemas de evaluacion automatica de metadata.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationConceptSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar parcialmente concepto de schema de metadata',
        description='Actualiza parcialmente el concepto que agrupa schemas de evaluacion automatica de metadata.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationConceptSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Eliminar concepto de schema de metadata',
        description='Elimina un concepto de evaluacion y sus schemas asociados por cascada.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: MessageResponseSerializer, 404: OpenApiResponse(description='Concepto no encontrado.')},
    ),
)
class EvaluationConceptSCHEMAViewSet(viewsets.ModelViewSet):
    """Expone conceptos de evaluación junto con sus schemas relacionados."""

    def get_permissions(self):
        if (self.action == 'list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = EvaluationConceptSerializer
    queryset = EvaluationConcept.objects.all()
    action_serializers = {
        'list': EvaluationConceptListSerializerSCHEMA,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationConceptSCHEMAViewSet, self).get_serializer_class()

    def update(self, request, pk=None, project_pk=None):
        """Actualiza el concepto que agrupa schemas de metadata."""
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationConceptSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.concept = serializer.validated_data['concept']
        instance.save()
        return Response({"message": "success"}, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera un concepto con su vista detallada de schema."""
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationConceptListSerializerSCHEMA(instance)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """Elimina un concepto de schema por identificador."""
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"}, status=HTTP_200_OK)

@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_EXPERT_METADATA_TAG,
        summary='Listar auto-preguntas de metadata',
        description='Lista preguntas de autoevaluacion junto con los schemas de metadata relacionados.',
        responses={200: EvaluationSelfQuestionListSerializerSCHEMA(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_EXPERT_METADATA_TAG,
        summary='Consultar auto-pregunta de metadata',
        description='Recupera una auto-pregunta con sus schemas relacionados.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationSelfQuestionListSerializerSCHEMA, 404: OpenApiResponse(description='Auto-pregunta no encontrada.')},
    ),
    create=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Crear auto-pregunta de metadata',
        description='Crea una pregunta de autoevaluacion usada para alimentar la evaluacion automatica de metadata.',
        request=EvaluationSelfQuestionSerializer,
        responses={201: EvaluationSelfQuestionSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar auto-pregunta de metadata',
        description='Actualiza la descripcion local e inglesa de una auto-pregunta.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationSelfQuestionSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar parcialmente auto-pregunta de metadata',
        description='Operacion generada por router. Se recomienda usar PUT porque el metodo custom espera los campos principales.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationSelfQuestionSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Eliminar auto-pregunta de metadata',
        description='Elimina una auto-pregunta desde el ViewSet principal.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={204: OpenApiResponse(description='Auto-pregunta eliminada.')},
    ),
)
class EvaluationSelfQuestionSCHEMAViewSet(viewsets.ModelViewSet):
    """CRUD administrativo de auto-preguntas usadas en evaluación de metadata."""
    def get_permissions(self):
        if (self.action == 'list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = EvaluationSelfQuestionSerializer
    queryset = SelfEvaluationQuestions.objects.all()
    action_serializers = {
        'list': EvaluationSelfQuestionListSerializerSCHEMA,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationSelfQuestionSCHEMAViewSet, self).get_serializer_class()

    def update(self, request, pk=None, project_pk=None):
        """Actualiza el texto local e ingles de una auto-pregunta."""
        queryset = SelfEvaluationQuestions.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationSelfQuestionSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.description = serializer.validated_data['description']
        instance.descriptionEnglish = serializer.validated_data['descriptionEnglish']
        instance.evaluation_concept = serializer.validated_data['evaluation_concept']
        instance.save()
        return Response({'message':'Update questions successful','code':200,'data':serializer.data}, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera una auto-pregunta por identificador."""
        queryset = SelfEvaluationQuestions.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationSelfQuestionListSerializerSCHEMA(user)
        return Response(serializer.data, status=HTTP_200_OK)

@extend_schema_view(
    delete=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Eliminar auto-pregunta de evaluacion',
        description='Borra una auto-pregunta por su identificador usando la ruta legacy manual.',
        responses={200: MessageResponseSerializer},
    )
)
class DeleteSelfEvaluationGenegircView(DestroyAPIView):
    """Elimina auto-preguntas fuera del router principal de schemas."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = EvaluationSelfQuestionSerializer

    @extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Eliminar auto-pregunta de evaluacion',
        description='Borra una auto-pregunta por su identificador usando la ruta legacy manual.',
        parameters=[
            EXPERT_EVALUATION_PK_PARAMETER,
        ],
        responses={200: MessageResponseSerializer},
    )
    def destroy(self, request, *args, **kwargs):
        """Borra una auto-pregunta por su `pk`."""
        queryset = SelfEvaluationQuestions.objects.all()
        instance = get_object_or_404(queryset, pk=kwargs.get('pk'))
        instance.delete()
        return Response({'message': 'Delete successful', 'code': 200}, status=HTTP_200_OK)


@extend_schema_view(
    delete=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Eliminar relacion entre metadata y auto-pregunta',
        description='Quita la auto-pregunta asociada a un schema de metadata sin eliminar el schema.',
        responses={
            200: MessageResponseSerializer,
            400: MessageResponseSerializer,
        },
    )
)
class RelationshipBetweenMetadataQuestion(RetrieveUpdateDestroyAPIView):
    """Administra la relacion entre una regla de metadata y una auto-pregunta."""
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = RelationshipQuestionAndMetadata
    queryset = EvaluationMetadata.objects.all()
    http_method_names = ['put', 'delete', 'options']

    @extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Asociar metadata con auto-pregunta',
        description='Asocia un schema de metadata con una auto-pregunta para que la evaluacion automatica pueda relacionar ambos insumos.',
        request=RelationshipQuestionAndMetadata,
        responses={
            200: MessageResponseSerializer,
            400: MessageResponseSerializer,
        },
    )
    def put(self, request, *args, **kwargs):
        """Asocia una pregunta de autoevaluación con un schema de metadata."""
        serializer = RelationshipQuestionAndMetadata(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            schema = EvaluationMetadata.objects.get(id=serializer['id_schema'].value)
            schema.self_evaluation_question_id = serializer['id_question'].value
            schema.save()
        except Exception as e :
            print('error',e)
            return Response({'message':'Error to update relationships', 'code':400}, status= HTTP_400_BAD_REQUEST)
        return Response({'message':'Update successful','code':200}, status= HTTP_200_OK)

    @extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Eliminar relacion entre metadata y auto-pregunta',
        description='Quita la auto-pregunta asociada a un schema de metadata sin eliminar el schema.',
        parameters=[
            EXPERT_EVALUATION_PK_PARAMETER,
        ],
        responses={
            200: MessageResponseSerializer,
            400: MessageResponseSerializer,
        },
    )
    def destroy(self, request, pk=None):
        """Desvincula la pregunta asociada a un schema de metadata."""
        try:
            schema = EvaluationMetadata.objects.get(id=pk)
            schema.self_evaluation_question_id = None
            schema.save()
        except Exception as e:
            print('error', e)
            return Response({'message': 'Error to delete relationships', 'code': 400}, status=HTTP_400_BAD_REQUEST)
        return Response({'message': 'Delete successful', 'code': 200}, status=HTTP_200_OK)

@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_EXPERT_METADATA_TAG,
        summary='Listar reglas de metadata evaluables',
        description='Lista schemas de metadata que el motor de evaluacion automatica puede calificar, con su peso y codigo.',
        responses={200: EvaluationMetadataSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_EXPERT_METADATA_TAG,
        summary='Consultar regla de metadata evaluable',
        description='Operacion legacy sin implementacion util en la vista actual.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationExpertEmptyResponseSerializer},
    ),
    create=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Crear regla de metadata evaluable',
        description='Crea un schema de metadata con peso, codigo y concepto asociado para evaluacion automatica.',
        request=EvaluationMetadataSerializer,
        responses={201: EvaluationMetadataSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar regla de metadata evaluable',
        description='Actualiza schema, descripcion, peso y codigo de una regla de metadata.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationMetadataRegisterSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Actualizar parcialmente regla de metadata evaluable',
        description='Operacion generada por router. Se recomienda usar PUT porque el metodo custom espera el payload completo.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        request=EvaluationMetadataRegisterSerializer,
        responses={200: MessageResponseSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_EXPERT_ADMIN_TAG,
        summary='Eliminar regla de metadata evaluable',
        description='Elimina una regla de metadata por identificador.',
        parameters=[EXPERT_EVALUATION_ID_PARAMETER],
        responses={200: MessageResponseSerializer, 404: OpenApiResponse(description='Regla no encontrada.')},
    ),
)
class EvaluationSchemaDataViewSet(viewsets.ModelViewSet):
    """CRUD de reglas de metadata usadas por la evaluación automática de OAs."""

    def get_permissions(self):
        if (self.action == 'list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = EvaluationMetadataSerializer
    queryset = EvaluationMetadata.objects.all()
    action_serializers = {
        'list': EvaluationMetadataSerializer,
    }
    def update(self, request, pk=None, project_pk=None):
        """Actualiza una regla de metadata respetando validaciones de unicidad."""
        queryset = EvaluationMetadata.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationMetadataRegisterSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.schema = serializer.validated_data['schema']
        instance.description = serializer.validated_data['description']
        instance.value_importance_schema = serializer.validated_data['value_importance_schema']
        instance.code = serializer.validated_data['code']
        instance.save()
        return Response({"message": "success"}, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        """Elimina una regla de metadata por identificador."""
        queryset = EvaluationMetadata.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"}, status=HTTP_200_OK)

@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_EXPERT_METADATA_TAG,
        summary='Consultar evaluacion automatica de metadata de un OA',
        description='Lista el resultado de evaluacion automatica de metadata para el objeto de aprendizaje indicado.',
        parameters=[EXPERT_EVALUATION_OA_ID_PARAMETER],
        responses={200: EvaluationAutomaticEvaluationSerializer(many=True)},
    )
)
class ListOAEvaluatedToAutomaticAPIView(ListAPIView):
    """Lista el resultado de evaluación automática de metadata para un OA."""
    permission_classes = [AllowAny]
    serializer_class = EvaluationAutomaticEvaluationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MetadataAutomaticEvaluation.objects.none()

        id = self.kwargs['pk']
        var1 = MetadataAutomaticEvaluation.objects.filter(
            learning_object__id=id
        ).distinct('learning_object')
        return var1

@extend_schema_view(
    post=extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Registrar respuestas de autoevaluacion de metadata',
        description='Guarda respuestas de autoevaluacion enviadas por el docente durante la carga o adaptacion de un OA.',
        request=MetadataSelfQuestionRequestSerializer,
        responses={
            200: MessageResponseSerializer,
            404: MessageResponseSerializer,
        },
    )
)
class CreateMetadataAssessmentSelfQuestion(ListCreateAPIView):
    """Guarda las respuestas de autoevaluación al subir un OA."""
    permission_classes = [IsAuthenticated, IsTeacherUser]
    serializer_class = MetadataSelfQuestionRequestSerializer
    http_method_names = ['post', 'options']

    @extend_schema(
        tags=EVALUATION_EXPERT_TAG,
        summary='Registrar respuestas de autoevaluacion de metadata',
        description='Guarda respuestas de autoevaluacion enviadas por el docente durante la carga o adaptacion de un OA.',
        request=MetadataSelfQuestionRequestSerializer,
        responses={
            200: MessageResponseSerializer,
            404: MessageResponseSerializer,
        },
    )
    def create(self, request, *args, **kwargs):
        """Persiste las respuestas de auto-preguntas enviadas por el docente."""
        try:
            selfQuestions = request.data['answerQuestion']
            for question in selfQuestions:
                modelmetadataSchemaQuestionQuialification = MetadataSchemaQuestionQualification.objects.create(
                    self_evaluation_question_id=question['idQuestion'],
                    qualification=convertResponseEvalution(question['answer']),
                    learning_object_file_id=request.data['learning_object_id'],
                )
                modelmetadataSchemaQuestionQuialification.save()
            return Response({'message': 'save data successful', 'code':200}, status=HTTP_200_OK)
        except Exception as e :
            print(e)
            return Response({'message':'Error saving assessments', 'code':400}, status=HTTP_404_NOT_FOUND)

def convertResponseEvalution(answer):
    """Convierte respuestas textuales de autoevaluación al puntaje persistido."""
    if answer == 'yes':
        return 1
    if answer == 'no':
        return 0
    if answer == 'parcialmente':
        return 0.5
