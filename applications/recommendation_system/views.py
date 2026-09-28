"""Vistas del sistema de recomendación.

El módulo principal expone el endpoint que arma recomendaciones de objetos de
aprendizaje para un usuario autenticado. La respuesta combina varias fuentes:
- recomendaciones derivadas de interacciones previas del usuario
- recomendaciones por afinidad entre perfil de preferencias y evaluaciones
  expertas de los OAs

La implementación privilegia resiliencia frente a datos incompletos: cuando una
fuente falla o devuelve una estructura inesperada, el flujo intenta degradarse
a listas vacías en lugar de romper el endpoint completo.
"""

import logging

from applications.recommendation_system.recommended import ItemsRecomended
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert
from applications.learning_object_metadata.serializers import LearningObjectMetadataPopularSerializer, ROANumberPaginationPopular
from django.shortcuts import render
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework.views import APIView
from applications.recommendation_system.dataset_generator import DataSetGenerator
from applications.user.mixins import IsCollaboratingExpertUser, IsStudentUser, IsTeacherUser
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)

dataset_generator = DataSetGenerator()
recommended = ItemsRecomended()
logger = logging.getLogger(__name__)

RECOMMENDATION_TAG = ['Recommendation System']


@extend_schema_view(
    get=extend_schema(
        tags=RECOMMENDATION_TAG,
        summary='Listar objetos de aprendizaje recomendados',
        description=(
            'Devuelve hasta ocho objetos de aprendizaje recomendados para el '
            'usuario autenticado. La recomendacion combina interacciones previas '
            'del usuario, como likes o visualizaciones, con afinidad entre sus '
            'preferencias y las evaluaciones expertas de los objetos de '
            'aprendizaje. Si los datasets auxiliares no tienen informacion '
            'suficiente o ocurre un error controlado, el endpoint responde una '
            'lista vacia en lugar de romper el flujo.'
        ),
        responses={
            200: LearningObjectMetadataPopularSerializer(many=True),
            401: OpenApiResponse(description='No autenticado. Se requiere token valido.'),
            403: OpenApiResponse(description='Usuario autenticado sin rol permitido para recomendaciones.'),
        },
    )
)
class LearningObjectRecommended(ListAPIView):
    """Devuelve recomendaciones personalizadas para usuarios autenticados.

    La vista combina dos estrategias:
    - recomendaciones por comportamiento previo, derivadas de likes u otras
      interacciones ya procesadas por `ItemsRecomended`
    - recomendaciones por afinidad entre el perfil del usuario y promedios de
      conceptos calculados sobre evaluaciones expertas

    El queryset final solo expone OAs públicos y excluye los que el usuario ya
    ha visto según el dataset auxiliar del módulo.
    """

    permission_classes = (IsAuthenticated,(IsStudentUser|IsTeacherUser|IsCollaboratingExpertUser))
    serializer_class = LearningObjectMetadataPopularSerializer
    pagination_class = None

    def get_queryset(self):
        """Construye la recomendacion final y degrada a `[]` ante errores.

        El flujo depende de varios datasets auxiliares. Si cualquiera devuelve
        un tipo inesperado o datos insuficientes para calcular el perfil del
        usuario, la vista opta por responder una lista vacía en lugar de
        propagar la excepción al cliente.
        """

        if getattr(self, "swagger_fake_view", False):
            return EvaluationCollaboratingExpert.objects.none()

        try:
            user = self.request.user
            learning_objects_recommended_by_liked = recommended.user_learning_object_recomended_liked(user)
            if not isinstance(learning_objects_recommended_by_liked, list):
                learning_objects_recommended_by_liked = []
            oa_viewed = dataset_generator.LearningObjectView(user)
            if not isinstance(oa_viewed, list):
                oa_viewed = []
            df_my_preferences = dataset_generator.user_profile_dataset(user)
            if not hasattr(df_my_preferences, "empty") or df_my_preferences.empty:
                return []
            required_preference_columns = {"preferences_are", "priority", "Total"}
            if not required_preference_columns.issubset(df_my_preferences.columns):
                return []
            userAveragePriority = self.get_user_preferences_value(
                df_my_preferences.groupby('preferences_are')['priority'].sum(),
                df_my_preferences.groupby('preferences_are')['Total'].sum()
            )
            if not isinstance(userAveragePriority, list):
                return []
            learningObjectAverageArea = dataset_generator.learning_object_concept_dataset()
            learning_objects_recommended_by_expert = self.recomended(learningObjectAverageArea, userAveragePriority)
            if not isinstance(learning_objects_recommended_by_expert, list):
                learning_objects_recommended_by_expert = []
            resultRecomendations= list(set(learning_objects_recommended_by_liked) | set(learning_objects_recommended_by_expert))
            # Delete learning objects already views
            results = [i for i in resultRecomendations if i not in oa_viewed]
            oa_recommended = EvaluationCollaboratingExpert.objects.filter(
                learning_object__id__in = results,
                learning_object__public=True,
            ).order_by('-learning_object__id').distinct('learning_object__id')[:8]
            return oa_recommended
        except (AttributeError, KeyError, TypeError, ValueError, IndexError, RuntimeError):
            logger.exception(
                "Error construyendo recomendaciones para el usuario %s",
                getattr(getattr(self, "request", None), "user", None) and getattr(self.request.user, "id", None),
            )
            return []

    def recomended(self, df_oa,df_user):
        """Filtra OAs cuyos promedios por concepto cumplen el perfil del usuario.

        `df_oa` representa el dataset agregado de conceptos por objeto de
        aprendizaje. `df_user` contiene los umbrales calculados a partir de las
        preferencias del usuario. Solo se recomienda un OA si cumple o supera
        todos los valores requeridos en las cuatro áreas evaluadas.
        """

        try:
            if not hasattr(df_oa, "empty") or df_oa.empty:
                return []
            required_columns = {"oaId", "concept", "average"}
            if not required_columns.issubset(df_oa.columns):
                return []
            if not isinstance(df_user, list) or len(df_user) < 4:
                return []
            oaId = df_oa['oaId'].unique()
            df_oa = df_oa.groupby(['oaId','concept'])['average'].sum()
            learning_objects = []
            for id in oaId:
                oa = df_oa.loc[id]
                oa = oa.to_dict()
                if(oa['Nivel De Interactividad'] >= df_user[0]['Nivel De Interactividad'] and
                    oa['Recursos Digitales Auditivos'] >= df_user[1]['Recursos Digitales Auditivos'] and
                    oa['Recursos Digitales Textuales'] >= df_user[2]['Recursos Digitales Textuales'] and 
                    oa['Recursos Digitales Visuales'] >= df_user[3]['Recursos Digitales Visuales']):
                    learning_objects.append(id)
            # Delete OA already views
            # results = [i for i in learning_objects + oa_viewed if i not in learning_objects or i not in oa_viewed]
            return learning_objects
        except (AttributeError, KeyError, TypeError, ValueError, IndexError):
            logger.exception("Error calculando recomendaciones por conceptos")
            return []

    def get_user_preferences_value(self,totalByUser,priority):
        """Convierte el perfil agregado del usuario en umbrales comparables.

        Recibe dos series agregadas: total de registros por área y suma de
        prioridad por área. El resultado es una lista de diccionarios, uno por
        área conceptual, que luego `recomended()` usa como mínimo esperado para
        aceptar o descartar un OA.
        """

        try:
            if not hasattr(totalByUser, "to_list") or not hasattr(priority, "to_list"):
                return []
            result = {}
            results =[]
            areas = ['Nivel De Interactividad','Recursos Digitales Auditivos','Recursos Digitales Textuales','Recursos Digitales Visuales']
            for index,data in enumerate(zip(totalByUser.to_list(),priority.to_list(),areas)):
                result = { areas[index]: (data[1]*2)/data[0] if data[0] else 0 }
                results.append(result)
            return results
        except (AttributeError, TypeError, ValueError, ZeroDivisionError):
            logger.exception("Error calculando el perfil de preferencias del usuario")
            return []


@extend_schema_view(
    get=extend_schema(
        tags=RECOMMENDATION_TAG,
        summary='Probar generador de datasets',
        description=(
            'Endpoint legacy de diagnostico. Actualmente no genera archivos ni '
            'recalcula datasets en tiempo de ejecucion; solo devuelve un mensaje '
            'fijo de exito. La ruta esta comentada en `urls.py`, por lo que no '
            'forma parte del contrato activo salvo que se reactive.'
        ),
        responses={
            200: inline_serializer(
                name='DatasetGeneratorLegacyResponse',
                fields={
                    'message': serializers.CharField(),
                    'status': serializers.CharField(),
                },
            )
        },
    )
)
class DataSetGeneratorView(APIView):
    """Endpoint legacy de prueba para el generador de datasets.

    Hoy no ejecuta tareas reales: conserva comentarios históricos con llamadas
    de diagnóstico y responde un mensaje fijo. Su valor actual es más cercano a
    un placeholder o punto de prueba manual que a un endpoint de negocio.
    """

    # permission_classes = (IsAuthenticated,IsStudentUser,)
    permission_classes = [AllowAny,]

    def get(self, request, format=None):
        """Responde exitosamente sin generar datasets en tiempo de ejecución."""

        # user = self.request.user
        # dataset_generator.user_profile_dataset(user)
        # dataset_generator.users_profile_dataset()
        # dataset_generator.learning_object_concept_dataset()
        # dataset_generator.learning_object_question_dataset()
        # df = pd.read_csv("user.csv", sep=";", quoting=3)
        return Response({"message":"Dataset successfully created","status":"Ok"}, status=HTTP_200_OK)

        