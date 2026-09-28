"""Vistas para registrar y consultar interacciones sobre objetos de aprendizaje.

Este módulo separa interacciones por usuario de contadores agregados:

- `InteractionAPIView` administra likes por usuario y OA
- `GetUpdateDownloadNumber` y `CreateDownload` mantienen descargas por usuario
- `CreateViewInteraction` y `GetUpdateViewNumberView` mantienen vistas agregadas
- `MostLikeLearningObjects` y `LearingObjectLike` exponen rankings publicos
- `UserRefTokenInteraction` valida una clave compartida y genera un token de referencia
"""

import logging
import shortuuid
from django.db.models import Case, Count, IntegerField, When
from django.http.response import Http404
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView, ListCreateAPIView
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.interaction.models import Interaction, ViewInteraction
from applications.interaction.serializers import InteractionAllService, InteractionSerializer, InteractionMostLiked, \
    InteractionViewCreateSerializer, InteractionViewSerializer, UserRefSerializer, \
    InteractionLikeUpdateSerializer, InteractionDownloadUpdateSerializer
from applications.learning_object_metadata.serializers import LearningObjectMetadataAllSerializer
from applications.user.mixins import IsStudentUser, IsTeacherUser, IsCollaboratingExpertUser
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)

from applications.helpers_functions.env_compat import get_key_ref


logger = logging.getLogger(__name__)


INTERACTION_TAG = ['Interaction']
INTERACTION_LIKE_TAG = ['Interaction Likes']
INTERACTION_DOWNLOAD_TAG = ['Interaction Downloads']
INTERACTION_VIEW_TAG = ['Interaction Views']
INTERACTION_REF_TAG = ['Interaction Reference']

INTERACTION_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador interno de la fila Interaction que relaciona un usuario con un objeto de aprendizaje.',
)
LEARNING_OBJECT_PK_PARAMETER = OpenApiParameter(
    'pk',
    int,
    OpenApiParameter.PATH,
    description='Identificador del objeto de aprendizaje sobre el que se consulta o actualiza la interacción.',
)

InteractionMessageSerializer = inline_serializer(
    name='InteractionMessage',
    fields={
        'message': serializers.CharField(),
        'code': serializers.IntegerField(required=False),
    },
)

DownloadCountResponseSerializer = inline_serializer(
    name='DownloadCountResponse',
    fields={
        'message': serializers.CharField(),
        'number': serializers.IntegerField(),
    },
)

InteractionViewErrorSerializer = inline_serializer(
    name='InteractionViewError',
    fields={
        'message': serializers.CharField(),
    },
)

InteractionRefResponseSerializer = inline_serializer(
    name='InteractionRefResponse',
    fields={
        'message': serializers.CharField(),
        'code': serializers.IntegerField(),
        'reference': serializers.CharField(required=False),
    },
)


@extend_schema_view(
    list=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Listar interacciones',
        description=(
            'Endpoint conservado por compatibilidad del router. La implementación actual no expone '
            'un listado real de interacciones y responde `404` con un mensaje simple.'
        ),
        responses={404: InteractionMessageSerializer},
    ),
    retrieve=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Obtener interacción por id',
        description=(
            'Devuelve la fila `Interaction` indicada. Esa fila representa la relación entre un usuario '
            'y un objeto de aprendizaje, incluyendo si tiene like y cuántas descargas registra.'
        ),
        parameters=[INTERACTION_ID_PARAMETER],
        responses={
            200: InteractionAllService,
            404: OpenApiResponse(description='Interacción no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Crear interacción de like',
        description=(
            'Crea la relación usuario-OA con el estado `liked` recibido. Si el usuario ya tiene '
            'una interacción para ese objeto, se rechaza para evitar duplicar la relación.'
        ),
        request=InteractionSerializer,
        responses={
            200: OpenApiResponse(response=InteractionAllService, description='Interacción creada correctamente.'),
            400: OpenApiResponse(
                response=InteractionMessageSerializer,
                description='El usuario ya tiene una interacción registrada para ese OA.',
            ),
        },
    ),
    update=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Actualizar like de una interacción',
        description=(
            'Actualiza únicamente el campo `liked` de una fila `Interaction` existente. No cambia '
            'el usuario, el objeto de aprendizaje ni el contador de descargas.'
        ),
        request=InteractionLikeUpdateSerializer,
        parameters=[INTERACTION_ID_PARAMETER],
        responses={
            200: InteractionAllService,
            404: OpenApiResponse(description='Interacción no encontrada.'),
        },
    ),
    partial_update=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Actualizar parcialmente una interacción',
        description=(
            'Mantiene compatibilidad con PATCH para cambiar el estado del like. Internamente usa '
            'el mismo contrato reducido que el update completo.'
        ),
        request=InteractionLikeUpdateSerializer,
        parameters=[INTERACTION_ID_PARAMETER],
        responses={
            200: InteractionAllService,
            404: OpenApiResponse(description='Interacción no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Eliminar interacción',
        description=(
            'Elimina la fila `Interaction`. Al hacerlo se pierden también el estado de like y el '
            'contador de descargas asociados a esa relación usuario-OA.'
        ),
        parameters=[INTERACTION_ID_PARAMETER],
        responses={200: InteractionMessageSerializer},
    ),
)
class InteractionAPIView(viewsets.ModelViewSet):
    """CRUD de likes sobre objetos de aprendizaje por usuario autenticado.

    Cada fila representa la relación entre un usuario y un OA. En este modulo
    esa relación se reutiliza también para guardar descargas, por eso crear un
    like implica crear la fila base de interacción.
    """

    serializer_class = InteractionAllService
    queryset = Interaction.objects.all()

    def get_permissions(self):

        if self.action=='list' or self.action=='retrieve':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """Crea el registro de like para el usuario y OA indicados.

        Si la relación usuario-OA ya existe, responde error para evitar
        duplicados y mantener un solo registro por persona y objeto.
        """
        serializer = InteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        learning_object = serializer.validated_data['learning_object']
        isLiked = Interaction.objects.filter(
            learning_object=learning_object,
            user__id=user.id
        )
        if isLiked.exists():
            return Response({"message": "Learning Object is already liked"},status=HTTP_400_BAD_REQUEST)

        instance = Interaction.objects.create(
            liked= serializer.validated_data['liked'],
            learning_object= learning_object,
            user=user
        )
        instance.save()
        serializer = InteractionAllService(instance)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """Actualiza solo el estado `liked` de una interacción existente.

        No modifica descargas ni cambia el OA asociado; solo alterna el like
        dentro de una fila ya creada.
        """
        queryset = Interaction.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = InteractionLikeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.liked = serializer.validated_data['liked']
        instance.save()
        serializer = InteractionAllService(instance)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera una interacción concreta por su identificador.

        Se usa para consultar el estado actual de la relación usuario-OA cuando
        ya se conoce el `pk` de la interacción.
        """
        queryset = Interaction.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = InteractionAllService(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """Elimina el registro de like o interacción indicado por `pk`.

        Al borrar la fila desaparecen también los contadores de descarga
        asociados a esa misma relación usuario-OA.
        """
        queryset = Interaction.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)

    def list(self, request):
        return Response({"message": "Not found"},status=HTTP_404_NOT_FOUND)


@extend_schema_view(
    get=extend_schema(
        tags=INTERACTION_DOWNLOAD_TAG,
        summary='Obtener total de descargas de un OA',
        description=(
            'Suma el campo `downloaded` de todas las interacciones registradas para el OA indicado. '
            'El resultado es un total agregado, no un detalle por usuario.'
        ),
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={200: DownloadCountResponseSerializer},
    ),
    put=extend_schema(
        tags=INTERACTION_DOWNLOAD_TAG,
        summary='Incrementar descargas de un OA para el usuario actual',
        description=(
            'Busca la interacción del usuario autenticado con el OA indicado en la URL e incrementa '
            'en uno el valor `downloaded` enviado. Si la relación usuario-OA no existe, responde error.'
        ),
        request=InteractionDownloadUpdateSerializer,
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: OpenApiResponse(
                response=InteractionAllService(many=True),
                description='Interacción actualizada con el nuevo contador de descargas.',
            ),
            400: OpenApiResponse(
                response=InteractionMessageSerializer,
                description='No existe una interacción previa que pueda actualizarse.',
            ),
        },
    ),
    patch=extend_schema(
        tags=INTERACTION_DOWNLOAD_TAG,
        summary='Incrementar descargas de un OA para el usuario actual',
        description=(
            'Alias PATCH expuesto por la vista generica. Usa el mismo contrato de actualización '
            'que PUT para incrementar el contador de descargas.'
        ),
        request=InteractionDownloadUpdateSerializer,
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: InteractionAllService(many=True),
            400: InteractionMessageSerializer,
        },
    ),
)
class GetUpdateDownloadNumber(RetrieveUpdateAPIView):
    """Lee y actualiza el total de descargas asociado a un OA.

    `GET` suma el contador `downloaded` de todas las interacciones del OA.
    `PUT` incrementa el contador del usuario autenticado dentro de su propia
    fila de interacción.
    """
    serializer_class = InteractionDownloadUpdateSerializer
    queryset = Interaction.objects.all()

    def get_permissions(self):
        permission_classes = None
        if self.request.method == 'PUT':
            permission_classes = [IsAuthenticated, IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]
        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    @extend_schema(
        tags=INTERACTION_DOWNLOAD_TAG,
        summary='Incrementar descargas de un OA para el usuario actual',
        description=(
            'Busca la interacción del usuario autenticado con el OA indicado en la URL e incrementa '
            'en uno el valor `downloaded` enviado. Si la relación usuario-OA no existe, responde error.'
        ),
        request=InteractionDownloadUpdateSerializer,
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: OpenApiResponse(
                response=InteractionAllService(many=True),
                description='Interacción actualizada con el nuevo contador de descargas.',
            ),
            400: OpenApiResponse(
                response=InteractionMessageSerializer,
                description='No existe una interacción previa que pueda actualizarse.',
            ),
        },
    )
    def update(self, request, *args, **kwargs):
        """Incrementa las descargas del usuario autenticado para el OA consultado.

        Espera que la fila `Interaction` del usuario ya exista; si no existe,
        la vista responde error y el cliente debe crearla por el flujo base.
        """
        serializer = InteractionDownloadUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        interaction_update = Interaction.objects.filter(learning_object_id = kwargs.get('pk'), user__id=user.id)
        if interaction_update:
            number_downloaded = serializer.validated_data['downloaded']
            number_downloaded = int(number_downloaded) + 1
            interaction_update[0].downloaded = number_downloaded
            interaction_update[0].save()
            serializer = InteractionAllService(interaction_update, many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        return Response({'message':'Error update Count Download'}, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=INTERACTION_DOWNLOAD_TAG,
        summary='Obtener total de descargas de un OA',
        description=(
            'Suma el campo `downloaded` de todas las interacciones registradas para el OA indicado. '
            'El resultado es un total agregado, no un detalle por usuario.'
        ),
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={200: DownloadCountResponseSerializer},
    )
    def get(self, request, *args, **kwargs):
        """Retorna la suma total de descargas registradas para un OA.

        El valor expuesto es agregado; no distingue cuantas descargas hizo cada
        usuario individualmente.
        """
        interactions = Interaction.objects.filter(learning_object_id = kwargs.get('pk'))
        number_downloaded = 0
        if len(interactions) > 1 :
            for interaction in interactions:
                number_downloaded = number_downloaded + int(interaction.downloaded)
        elif len(interactions) == 1:
            number_downloaded = interactions[0].downloaded

        return Response({'message': 'success', 'number': number_downloaded},status=HTTP_200_OK)


class GetLikedLearningObjetById(APIView):
    """Recupera la interacción del usuario actual con un OA concreto.

    Este endpoint se usa para responder rápido si el usuario ya marco o no un
    OA como liked dentro de su propia relación.
    """
    permission_classes = [IsAuthenticated,  IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]

    def get_object(self, pk):
        """Busca la relación usuario-OA y eleva 404 si no existe."""
        try:
            return Interaction.objects.get(learning_object__id=pk,user__id=self.request.user.id)
        except Interaction.DoesNotExist:
            raise Http404

    @extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Obtener like del usuario para un OA',
        description=(
            'Consulta la fila `Interaction` del usuario autenticado para saber si ya marcó como liked '
            'el objeto de aprendizaje recibido en la ruta.'
        ),
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: InteractionAllService,
            404: OpenApiResponse(description='Interacción no encontrada para el usuario y OA indicados.'),
        },
    )
    def get(self, request, pk, format=None):
        """Devuelve el estado de like del usuario autenticado para un OA."""
        snippet = self.get_object(pk)
        serializer = InteractionAllService(snippet)
        return Response(serializer.data)


@extend_schema_view(
    post=extend_schema(
        tags=INTERACTION_DOWNLOAD_TAG,
        summary='Crear registro de descarga',
        description=(
            'Crea la interacción inicial de descarga para el usuario autenticado. Si la relación '
            'usuario-OA ya existe, reutiliza esa fila y actualiza el contador `downloaded`.'
        ),
        request=InteractionSerializer,
        responses={200: OpenApiResponse(response=InteractionAllService, description='Registro de descarga creado o actualizado.')},
    )
)
class CreateDownload(CreateAPIView):
    """Crea o inicializa el registro de descargas del usuario sobre un OA.

    Si la relación usuario-OA ya existe, reutiliza esa fila y actualiza el
    contador `downloaded`; si no existe, crea la fila desde cero.
    """

    permission_classes = [IsAuthenticated, IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]
    serializer_class = InteractionSerializer

    @extend_schema(
        tags=INTERACTION_DOWNLOAD_TAG,
        summary='Crear registro de descarga',
        description=(
            'Crea la interacción inicial de descarga para el usuario autenticado. Si la relación '
            'usuario-OA ya existe, reutiliza esa fila y actualiza el contador `downloaded`.'
        ),
        request=InteractionSerializer,
        responses={200: OpenApiResponse(response=InteractionAllService, description='Registro de descarga creado o actualizado.')},
    )
    def create(self, request, *args, **kwargs):
        """Crea la relación de descarga o reutiliza una interacción ya existente.

        Sirve como punto de entrada cuando todavía no existe la fila de
        interacción y por eso `GetUpdateDownloadNumber` no puede incrementar.
        """
        serializer = InteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user

        learning_object = serializer.validated_data['learning_object']

        exist_liked = Interaction.objects.filter(
            learning_object=learning_object,
            user__id=user.id
        )

        if exist_liked.exists():
            exist_liked[0].downloaded =serializer.validated_data['downloaded']
            exist_liked[0].save()
            serializer = InteractionAllService(exist_liked,many=True)
            return Response(serializer.data, status=HTTP_200_OK)

        instance = Interaction.objects.create(
            downloaded=serializer.validated_data['downloaded'],
            learning_object=learning_object,
            user=user
        )
        instance.save()
        serializer = InteractionAllService(instance)
        return Response(serializer.data, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Listar OAs públicos con más likes',
        description=(
            'Calcula un ranking desde las interacciones con `liked=True`, selecciona hasta cuatro '
            'objetos de aprendizaje y devuelve su metadata pública.'
        ),
        responses={200: LearningObjectMetadataAllSerializer(many=True)},
    ),
)
class MostLikeLearningObjects(ListAPIView):
    """Lista los OAs públicos con mayor cantidad de likes.

    El ranking se calcula agregando filas `Interaction(liked=True)` y luego se
    limita a cuatro objetos visibles públicamente.
    """
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataAllSerializer

    def get_queryset(self):
        """Agrega likes por OA y limita la salida a los cuatro primeros.

        El queryset final devuelve `LearningObjectMetadata`, no el agregado
        crudo de interacciones.
        """
        interactions = Interaction.objects.filter(
            liked=True,
            learning_object__public=True,
        ).values('learning_object_id').annotate(
            total=Count('learning_object_id'),
        ).order_by('-total', '-learning_object_id')[:4]

        learning_object_ids = [
            int(interaction['learning_object_id'])
            for interaction in interactions
        ]
        if not learning_object_ids:
            return LearningObjectMetadata.objects.none()

        order_by_rank = Case(
            *[
                When(id=learning_object_id, then=position)
                for position, learning_object_id in enumerate(learning_object_ids)
            ],
            output_field=IntegerField(),
        )
        return LearningObjectMetadata.objects.filter(
            public=True,
            id__in=learning_object_ids,
        ).order_by(order_by_rank)


@extend_schema_view(
    get=extend_schema(
        tags=INTERACTION_LIKE_TAG,
        summary='Obtener total de likes de un OA',
        description=(
            'Devuelve el agregado de likes para un solo objeto de aprendizaje. La respuesta contiene '
            'el id del OA y el total calculado desde las filas `Interaction(liked=True)`.'
        ),
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={200: InteractionMostLiked(many=True)},
    ),
)
class LearingObjectLike(ListAPIView):
    """Devuelve el total de likes de un OA concreto.

    A diferencia de `MostLikeLearningObjects`, aqui la respuesta es el agregado
    númerico por un solo objeto, no la metadata completa del OA.
    """
    permission_classes = [AllowAny]
    serializer_class = InteractionMostLiked

    def get_queryset(self):
        """Agrega likes únicamente para el OA indicado en la URL."""
        if getattr(self, 'swagger_fake_view', False):
            return Interaction.objects.none()

        interaction = Interaction.objects.filter(learning_object_id=self.kwargs['pk'], liked=True)
        interaction_filter = interaction.values('learning_object_id').annotate(total=Count('learning_object_id')).order_by('-total')
        return interaction_filter


@extend_schema_view(
    post=extend_schema(
        tags=INTERACTION_VIEW_TAG,
        summary='Crear contador de vistas',
        description=(
            'Crea el registro inicial en `ViewInteraction` para almacenar el total de vistas de un OA. '
            'Este contador es agregado y no depende del usuario autenticado.'
        ),
        request=InteractionViewCreateSerializer,
        responses={200: InteractionViewSerializer},
    )
)
class CreateViewInteraction(CreateAPIView):
    """Crea el contador inicial de vistas para un OA.

    Las vistas se almacenan en `ViewInteraction`, separadas de `Interaction`,
    porque aquí no se modela una relación por usuario sino un total agregado.
    """
    permission_classes = [AllowAny]
    serializer_class = InteractionViewCreateSerializer

    @extend_schema(
        tags=INTERACTION_VIEW_TAG,
        summary='Crear contador de vistas',
        description=(
            'Crea el registro inicial en `ViewInteraction` para almacenar el total de vistas de un OA. '
            'Este contador es agregado y no depende del usuario autenticado.'
        ),
        request=InteractionViewCreateSerializer,
        responses={200: InteractionViewSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Persiste un registro inicial de vistas para el OA recibido."""
        serializer = InteractionViewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interaction_view = ViewInteraction.objects.create(
            view=serializer.validated_data['view'],
            learning_object=serializer.validated_data['learning_object']
        )
        interaction_view.save()
        view_interaction_s = InteractionViewSerializer(interaction_view)
        return Response(view_interaction_s.data, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=INTERACTION_VIEW_TAG,
        summary='Obtener contador de vistas de un OA',
        description=(
            'Busca el registro `ViewInteraction` asociado al OA recibido y devuelve su contador de '
            'vistas. Si no existe un registro previo, responde error.'
        ),
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: InteractionViewSerializer(many=True),
            400: InteractionViewErrorSerializer,
        },
    ),
    put=extend_schema(
        tags=INTERACTION_VIEW_TAG,
        summary='Actualizar contador de vistas de un OA',
        description=(
            'Reemplaza el valor guardado en `ViewInteraction` por el numero enviado en el cuerpo. '
            'No suma automaticamente; el cliente debe enviar el total final que desea persistir.'
        ),
        request=InteractionViewCreateSerializer,
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: InteractionViewSerializer(many=True),
            400: InteractionViewErrorSerializer,
        },
    ),
    patch=extend_schema(
        tags=INTERACTION_VIEW_TAG,
        summary='Actualizar contador de vistas de un OA',
        description=(
            'Alias PATCH expuesto por la vista generica. Usa el mismo contrato que PUT para reemplazar '
            'el contador de vistas del OA.'
        ),
        request=InteractionViewCreateSerializer,
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: InteractionViewSerializer(many=True),
            400: InteractionViewErrorSerializer,
        },
    ),
)
class GetUpdateViewNumberView(RetrieveUpdateAPIView):
    """Lee y actualiza el contador agregado de vistas de un OA.

    A diferencia de descargas y likes, este contador no es por usuario. La
    vista asume una sola fila `ViewInteraction` por OA.
    """

    permission_classes = [AllowAny]
    serializer_class = InteractionViewCreateSerializer
    queryset = ViewInteraction.objects.all()

    @extend_schema(
        tags=INTERACTION_VIEW_TAG,
        summary='Obtener contador de vistas de un OA',
        description=(
            'Busca el registro `ViewInteraction` asociado al OA recibido y devuelve su contador de '
            'vistas. Si no existe un registro previo, responde error.'
        ),
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: InteractionViewSerializer(many=True),
            400: InteractionViewErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """Devuelve el contador de vistas registrado para un OA."""
        view_interaction = ViewInteraction.objects.filter(learning_object=kwargs.get('pk'))
        if len(view_interaction) > 0:
            serializer = InteractionViewSerializer(view_interaction, many=True);
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({'message': 'error'}, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=INTERACTION_VIEW_TAG,
        summary='Actualizar contador de vistas de un OA',
        description=(
            'Reemplaza el valor guardado en `ViewInteraction` por el número enviado en el cuerpo. '
            'No suma automáticamente; el cliente debe enviar el total final que desea persistir.'
        ),
        request=InteractionViewCreateSerializer,
        parameters=[LEARNING_OBJECT_PK_PARAMETER],
        responses={
            200: InteractionViewSerializer(many=True),
            400: InteractionViewErrorSerializer,
        },
    )
    def update(self, request, *args, **kwargs):
        """Reemplaza el contador de vistas almacenado para el OA indicado.

        No incrementa automáticamente; persiste exactamente el valor enviado
        por el cliente.
        """
        serializer = InteractionViewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = ViewInteraction.objects.filter(learning_object=serializer.validated_data['learning_object'])
        if len(instance) > 0:
            instance[0].view = serializer.validated_data['view']
            instance[0].save()
            serializer_data = InteractionViewSerializer(instance, many=True)
            return Response(serializer_data.data, status=HTTP_200_OK)
        return Response({'message': 'error'}, status= HTTP_400_BAD_REQUEST)


class UserRefTokenInteraction(ListCreateAPIView):
    """Genera un token usado por el flujo `interaction-ref`.

    El endpoint valida una clave compartida de entorno (`KEY_REF`) antes de
    devolver un identificador aleatorio que otros flujos usan como referencia.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRefSerializer
    http_method_names = ['post', 'options']

    @extend_schema(
        tags=INTERACTION_REF_TAG,
        summary='Generar token de referencia de interacción',
        description=(
            'Valida la clave compartida `key_ref` contra la variable de entorno `KEY_REF`. Si coincide, '
            'genera una referencia aleatoria usada por flujos auxiliares del frontend.'
        ),
        request=UserRefSerializer,
        responses={
            200: OpenApiResponse(response=InteractionRefResponseSerializer, description='Referencia generada correctamente.'),
            404: OpenApiResponse(response=InteractionRefResponseSerializer, description='Clave inválida o KEY_REF no configurado.'),
        },
    )
    def post(self, request, *args, **kwargs):
        """Valida la clave compartida y retorna un token aleatorio si coincide.

        Si la variable de entorno no está configurada, registra el problema en
        logs y responde error controlado en lugar de lanzar un 500.
        """
        serializer = UserRefSerializer(data=request.data)
        if serializer.is_valid():
            configured_key_ref = get_key_ref()
            if configured_key_ref is None:
                logger.error("KEY_REF no esta configurado para interaction-ref")
                return Response({'message':'Error', 'code':400}, status= HTTP_404_NOT_FOUND)
            if serializer.validated_data['key_ref'] == configured_key_ref:
                user_token = str(shortuuid.ShortUUID().random(length=64))
                return Response({'message':'successful', 'code':200,'reference':user_token},status= HTTP_200_OK)
        return Response({'message':'Error', 'code':400}, status= HTTP_404_NOT_FOUND)


class UserRefTokenInteractionLegacy(UserRefTokenInteraction):
    """Alias legacy sin slash final para conservar compatibilidad del frontend."""

    @extend_schema(
        tags=INTERACTION_REF_TAG,
        operation_id='api_v1_interaction_ref_legacy_create',
        summary='Generar token de referencia de interacción legacy',
        description=(
            'Alias sin slash final de `interaction-ref/`. Se mantiene para clientes antiguos que '
            'consumen la ruta legacy.'
        ),
        request=UserRefSerializer,
        responses={
            200: InteractionRefResponseSerializer,
            404: InteractionRefResponseSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
