"""Vistas de configuración operativa para administración.

Este módulo expone endpoints para dos áreas principales:
- configuración del servidor de correo usado por la plataforma
- reglas de registro basadas en dominios de email y tipo de usuario

La mayoría de las rutas son administrativas. Algunas lecturas se dejan
publicas o con permisos más amplios porque sirven para decidir reglas de
registro antes de completar un alta de usuario.
"""

import logging

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND

from applications.settings.models import Email, OptionRegisterEmailExtension, EmailExtensionsTeacher, \
    EmailExtensionsExpert, EmailExtensionsStudent, UserTypeWithOption
from applications.settings.serializers import EmailSerializer, EmailDomainTeacherSerializer, \
    OptionRegisterEmailExtensionSerializer, EmailDomainExpertSerializer, EmailDomainStudentSerializer, \
    UserTypeWithOptionSerializer, EmailDomainTeacherCreateSerializer, EmailDomainExpertCreateSerializer, \
    EmailDomainStudentCreateSerializer, UserTypeWithOptionSerializerList, EmailDomainTypeSerializer, \
    EmailDomainListQuerySerializer, UserTypeOptionUpdateInputSerializer, EmailTestingConnectionSerializer
from applications.user.mixins import IsAdministratorUser, IsGeneralUser
from applications.user.emailManager import MAIL_DELIVERY_EXCEPTIONS
from applications.user.views import mail_aproved


logger = logging.getLogger(__name__)

SETTINGS_EMAIL_TAG = ['Settings Email']
SETTINGS_EMAIL_DOMAIN_TAG = ['Settings Email Domains']
SETTINGS_REGISTRATION_TAG = ['Settings Registration Rules']
USER_TYPE_PARAMETER = OpenApiParameter(
    name='type',
    type=str,
    location=OpenApiParameter.QUERY,
    enum=['TEACHER', 'EXPERT', 'STUDENT'],
    description='Tipo de usuario que selecciona la tabla de dominios a consultar o modificar.',
)
OPTION_PARAMETER = OpenApiParameter(
    name='option',
    type=int,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Identificador de la politica de registro usada para filtrar dominios.',
)
DOMAIN_PK_PARAMETER = OpenApiParameter(
    name='id',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador del recurso en la ruta. Internamente la vista lo recibe como `pk`.',
)

EMAIL_DOMAIN_CONFIG = {
    "TEACHER": (EmailExtensionsTeacher, EmailDomainTeacherSerializer, EmailDomainTeacherCreateSerializer),
    "EXPERT": (EmailExtensionsExpert, EmailDomainExpertSerializer, EmailDomainExpertCreateSerializer),
    "STUDENT": (EmailExtensionsStudent, EmailDomainStudentSerializer, EmailDomainStudentCreateSerializer),
}


def _get_email_domain_config(user_type):
    """Resuelve el trio modelo/serializer según el tipo de usuario validado.

    Centraliza el mapping para que create, list, update y delete de dominios
    compartan la misma selección de clases y no dupliquen `if/elif`.
    """
    return EMAIL_DOMAIN_CONFIG[user_type]


@extend_schema_view(
    get=extend_schema(
        tags=SETTINGS_EMAIL_TAG,
        summary='Consultar configuracion SMTP',
        description=(
            'Devuelve la configuracion SMTP persistida del sistema. La vista '
            'opera como recurso unico: toma el primer registro de `Email`. '
            'Requiere autenticacion y rol administrador.'
        ),
        responses={
            200: EmailSerializer,
            204: OpenApiResponse(description='No existe configuracion SMTP registrada.'),
        },
    ),
    post=extend_schema(
        tags=SETTINGS_EMAIL_TAG,
        summary='Actualizar configuracion SMTP',
        description=(
            'Actualiza parcialmente la configuracion SMTP existente. Si se envia '
            '`password`, el valor se cifra antes de guardarse; si no se envia, '
            'se conserva el password actual.'
        ),
        request=inline_serializer(
            name='EmailSettingsUpdateRequest',
            fields={
                'host': serializers.CharField(required=False),
                'username': serializers.CharField(required=False),
                'password': serializers.CharField(required=False),
                'port': serializers.CharField(required=False),
                'tls': serializers.BooleanField(required=False),
                'email_from': serializers.EmailField(required=False),
            },
        ),
        responses={
            201: EmailSerializer,
            400: OpenApiResponse(description='No existe configuracion SMTP o el payload es invalido.'),
        },
    ),
)
class EmailListCreateAPIView(generics.ListCreateAPIView):
    """Consulta y actualiza la configuración SMTP persistida del sistema.

    Aunque hereda de `ListCreateAPIView`, en la práctica opera como un recurso
    singleton: siempre trabaja sobre el primer registro de `Email`.
    """

    queryset = Email.objects.none()
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated, IsAdministratorUser]  # permisos autenticado y solo de admin

    def get(self, request):
        """Devuelve la configuración SMTP actual o un mensaje si no existe."""

        email = Email.objects.first()
        if email is None:
            return Response({"status": 204, "message": "The company don't have an assigned email"},
                            status=status.HTTP_200_OK)
        serializer = self.serializer_class(email)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Actualiza la configuración SMTP existente y recifra el password.

        Si el payload incluye un nuevo password, la vista lo cifra antes de
        guardar. Si no viene `password`, conserva el valor cifrado actual.
        """

        email_obj = Email.objects.first()
        if email_obj is None:
            return Response(
                {"status": "error", "message": "The company don't have an assigned email", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(instance=email_obj, data=request.data, partial=True)
        if serializer.is_valid():
            new_password = request.data.get('password')
            if new_password is not None:
                hashed_password = email_obj.encrypt_password(new_password)
                serializer.validated_data['password'] = hashed_password.decode('utf-8')
            else:
                serializer.validated_data['password'] = email_obj.password

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({'message': 'Error', 'error': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        tags=SETTINGS_EMAIL_DOMAIN_TAG,
        summary='Listar dominios de correo por tipo de usuario',
        description=(
            'Lista dominios configurados para docentes, expertos o estudiantes. '
            'El query param `type` decide que tabla se consulta y `option` '
            'permite filtrar por politica de registro.'
        ),
        parameters=[USER_TYPE_PARAMETER, OPTION_PARAMETER],
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='EmailDomainListResponse',
                    fields={
                        'message': serializers.CharField(),
                        'code': serializers.IntegerField(),
                        'data': serializers.ListField(child=serializers.DictField()),
                    },
                ),
                description='Listado de dominios segun el tipo de usuario solicitado.',
            ),
            404: OpenApiResponse(description='Parametros de consulta invalidos.'),
        },
    ),
    post=extend_schema(
        tags=SETTINGS_EMAIL_DOMAIN_TAG,
        summary='Crear dominio de correo',
        description=(
            'Crea un dominio para docentes, expertos o estudiantes. El campo '
            '`type` del payload selecciona la tabla destino. Requiere usuario '
            'administrador.'
        ),
        request=inline_serializer(
            name='EmailDomainCreateRequest',
            fields={
                'type': serializers.ChoiceField(choices=['TEACHER', 'EXPERT', 'STUDENT']),
                'domain': serializers.CharField(),
                'is_active': serializers.BooleanField(required=False),
                'option_register_email': serializers.IntegerField(),
            },
        ),
        responses={
            200: OpenApiResponse(description='Dominio creado correctamente.'),
            400: OpenApiResponse(description='Payload invalido o dominio duplicado.'),
        },
    ),
)
class EmailDomainListCreateAPIView(generics.ListCreateAPIView):
    """Lista o crea dominios permitidos/restringidos según tipo de usuario.

    La clase usa `type` como selector para reutilizar una sola vista sobre las
    tres tablas de dominios: docentes, expertos y estudiantes.
    """

    queryset = EmailExtensionsTeacher.objects.none()
    serializer_class = EmailDomainTypeSerializer

    def get_permissions(self):
        """Permite listado público y reserva altas a administradores."""

        permission_classes = None
        if self.request.method == 'POST':
            permission_classes = [IsAuthenticated, IsAdministratorUser ]
        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    @staticmethod
    def _error_response(message, status_code, errors=None):
        """Construye la respuesta legacy incluyendo errores del serializer."""
        response = {'message': message, 'code': 400}
        if errors:
            response['errors'] = errors
        return Response(response, status=status_code)

    def create(self, request, *args, **kwargs):
        """Crea un dominio en la tabla correspondiente al `type` recibido."""

        input_serializer = EmailDomainTypeSerializer(data=request.data)
        if not input_serializer.is_valid():
            return self._error_response('Create error', HTTP_400_BAD_REQUEST, input_serializer.errors)

        _, _, create_serializer_class = _get_email_domain_config(input_serializer.validated_data['type'])
        serializer = create_serializer_class(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'message':'Create Successful', 'code':200}, status=HTTP_200_OK)
        return self._error_response('Create error', HTTP_400_BAD_REQUEST, serializer.errors)

    def list(self, request, *args, **kwargs):
        """Lista dominios filtrados por tipo de usuario y opción de registro."""

        query_serializer = EmailDomainListQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return self._error_response('List error', HTTP_404_NOT_FOUND, query_serializer.errors)

        model_class, list_serializer_class, _ = _get_email_domain_config(query_serializer.validated_data['type'])
        option = query_serializer.validated_data.get('option')
        queryset = model_class.objects.filter(option_register_email=option).order_by('id')
        serializer = list_serializer_class(queryset, many=True)
        return Response({'message': 'List Successful', 'code': 200, "data": serializer.data}, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=SETTINGS_EMAIL_DOMAIN_TAG,
        summary='Listar dominios activos de docentes',
        description=(
            'Devuelve dominios activos de docentes. Es una ruta administrativa '
            'legacy usada para consultar rapidamente extensiones habilitadas.'
        ),
        responses={200: EmailDomainTeacherSerializer(many=True)},
    )
)
class EmailDomainListListAPIView(generics.ListAPIView):
    """Listado administrativo directo de dominios activos para docentes."""

    queryset = EmailExtensionsTeacher.objects.filter(is_active=True).order_by('id')
    serializer_class = EmailDomainTeacherSerializer
    permission_classes = [IsAuthenticated, IsAdministratorUser]  # permisos autenticado y solo de admin


class EmailDomainListView(generics.ListAPIView):
    """Versión legacy de detalle/listado por `pk` y `type`.

    La vista selecciona manualmente la tabla según `type` en query params y
    devuelve una lista con cero o un elemento. Mantiene respuestas legacy en
    lugar de apoyarse en un `RetrieveAPIView` convencional.
    """

    permission_classes = [IsAuthenticated, IsAdministratorUser]  # permisos autenticado y solo de admin

    def list(self, request, *args, **kwargs):
        """Devuelve el dominio solicitado desde la tabla indicada por `type`."""

        if request.query_params.get('type') == "TEACHER":
            instance = EmailExtensionsTeacher.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainTeacherSerializer(instance, many=True)
            return Response({'message':'List successful','code':200, 'data': serializer.data}, status=HTTP_200_OK)
        elif request.query_params.get('type') == "EXPERT":
            instance = EmailExtensionsExpert.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainTeacherSerializer(instance, many=True)
            return Response({'message':'List successful','code':200, 'data': serializer.data}, status=HTTP_200_OK)
        elif request.query_params.get('type') == "STUDENT":
            instance = EmailExtensionsStudent.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainTeacherSerializer(instance, many=True)
            return Response({'message':'List successful','code':200, 'data': serializer.data}, status=HTTP_200_OK)
        else:
            return Response({'message': 'List error', 'code': 400}, status=HTTP_404_NOT_FOUND)


# Esta segunda declaracion con el mismo nombre sobrescribe la clase anterior en
# el modulo. Se conserva porque forma parte del comportamiento heredado activo.
@extend_schema_view(
    delete=extend_schema(
        tags=SETTINGS_EMAIL_DOMAIN_TAG,
        summary='Eliminar dominio de correo',
        description=(
            'Elimina un dominio por `pk` en la tabla seleccionada con el query '
            'param `type`. La respuesta mantiene el formato legacy con '
            '`message` y `code`.'
        ),
        parameters=[DOMAIN_PK_PARAMETER, USER_TYPE_PARAMETER],
        responses={
            200: inline_serializer(
                name='EmailDomainDeleteResponse',
                fields={
                    'message': serializers.CharField(),
                    'code': serializers.IntegerField(),
                },
            ),
            404: OpenApiResponse(description='Tipo de usuario invalido.'),
        },
    )
)
class EmailDomainListView(generics.DestroyAPIView):
    """Elimina dominios de correo segun `pk` y `type` recibido en query params."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]  # permisos autenticado y solo de admin

    def destroy(self, request, *args, **kwargs):
        """Borra el dominio de la tabla resuelta por `type`."""

        query_serializer = EmailDomainTypeSerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return EmailDomainListCreateAPIView._error_response(
                'Delete error',
                HTTP_404_NOT_FOUND,
                query_serializer.errors,
            )

        model_class, _, _ = _get_email_domain_config(query_serializer.validated_data['type'])
        instance = model_class.objects.filter(pk=kwargs.get('pk'))
        instance.delete()
        return Response({'message':'Delete Success', 'code': 200}, status= HTTP_200_OK)


@extend_schema_view(
    put=extend_schema(
        tags=SETTINGS_EMAIL_DOMAIN_TAG,
        summary='Actualizar dominio de correo',
        description=(
            'Actualiza parcialmente un dominio existente en la tabla seleccionada '
            'por `type`. Aunque la ruta usa PUT, internamente la vista aplica '
            '`partial=True` para aceptar campos parciales.'
        ),
        parameters=[DOMAIN_PK_PARAMETER, USER_TYPE_PARAMETER],
        request=inline_serializer(
            name='EmailDomainUpdateRequest',
            fields={
                'domain': serializers.CharField(required=False),
                'is_active': serializers.BooleanField(required=False),
                'option_register_email': serializers.IntegerField(required=False),
            },
        ),
        responses={
            200: OpenApiResponse(description='Dominio actualizado correctamente.'),
            404: OpenApiResponse(description='Tipo invalido o dominio no encontrado.'),
        },
    ),
    patch=extend_schema(
        tags=SETTINGS_EMAIL_DOMAIN_TAG,
        summary='Actualizar parcialmente dominio de correo',
        description='Alias parcial para actualizar un dominio de correo segun el tipo de usuario.',
        parameters=[DOMAIN_PK_PARAMETER, USER_TYPE_PARAMETER],
        request=inline_serializer(
            name='EmailDomainPartialUpdateRequest',
            fields={
                'domain': serializers.CharField(required=False),
                'is_active': serializers.BooleanField(required=False),
                'option_register_email': serializers.IntegerField(required=False),
            },
        ),
        responses={
            200: OpenApiResponse(description='Dominio actualizado correctamente.'),
            404: OpenApiResponse(description='Tipo invalido o dominio no encontrado.'),
        },
    ),
)
class EmailDomainUpdateView(generics.UpdateAPIView):
    """Actualiza un dominio existente en la tabla seleccionada por `type`."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = EmailDomainTeacherCreateSerializer
    queryset = EmailExtensionsTeacher.objects.none()

    def get_serializer_class(self):
        """Devuelve el serializer de escritura acorde al `type` consultado."""

        user_type = self.request.query_params.get('type')
        if user_type in EMAIL_DOMAIN_CONFIG:
            return EMAIL_DOMAIN_CONFIG[user_type][2]
        return self.serializer_class

    def get_queryset(self):
        """Resuelve un queryset compatible con el `type` de la petición."""

        user_type = self.request.query_params.get('type')
        if user_type in EMAIL_DOMAIN_CONFIG:
            return EMAIL_DOMAIN_CONFIG[user_type][0].objects.all()
        return self.queryset

    def update(self, request, *args, **kwargs):
        """Aplica update parcial sobre el dominio identificado por `pk`."""

        query_serializer = EmailDomainTypeSerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return EmailDomainListCreateAPIView._error_response(
                'Update error',
                HTTP_404_NOT_FOUND,
                query_serializer.errors,
            )

        model_class, _, create_serializer_class = _get_email_domain_config(query_serializer.validated_data['type'])
        instance = model_class.objects.filter(pk=kwargs.get('pk')).first()
        if instance is None:
            return Response({'message': 'Update error', 'code': 400}, status=HTTP_404_NOT_FOUND)

        serializer = create_serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':'Successful','data':serializer.data})

@extend_schema_view(
    post=extend_schema(
        tags=SETTINGS_EMAIL_TAG,
        summary='Probar conexion SMTP',
        description=(
            'Usa la configuracion SMTP persistida e intenta enviar un correo de '
            'prueba al destinatario indicado.'
        ),
        request=EmailTestingConnectionSerializer,
        responses={
            200: inline_serializer(
                name='EmailTestingSuccessResponse',
                fields={
                    'code': serializers.IntegerField(),
                    'message': serializers.CharField(),
                },
            ),
            400: OpenApiResponse(description='Error de validacion o fallo controlado al enviar correo.'),
        },
    )
)
class sendEmailTestingConecction(CreateAPIView):
    """Prueba una conexión SMTP con credenciales enviadas en el payload."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = EmailTestingConnectionSerializer

    def post(self, request, *args, **kwargs):
        """Intenta enviar un correo de prueba y reporta errores controlados."""

        input_serializer = EmailTestingConnectionSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {'code': 400, 'message': 'Validation error', 'errors': input_serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        data = input_serializer.validated_data
        try:
            mail_aproved.sendEmailTesting(data['emailtest'])

            return Response({'code': 200, 'message': 'Email testing sent successfully'}, status=HTTP_200_OK)
        except MAIL_DELIVERY_EXCEPTIONS as e:
            logger.exception('Error en la prueba de conexion del servidor de correo')
            return Response({'code': 400, 'message': e.__str__()}, status=HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        tags=SETTINGS_REGISTRATION_TAG,
        summary='Listar politicas de registro por dominio',
        description=(
            'Devuelve las opciones globales que definen como se interpretan los '
            'dominios de correo: ALL, EXCEPT u ONLY.'
        ),
        responses={200: OptionRegisterEmailExtensionSerializer(many=True)},
    )
)
class OptionRegisterEmailExtensionView(ListAPIView):
    """Lista las opciones globales de política de registro por extensión."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = OptionRegisterEmailExtensionSerializer
    queryset = OptionRegisterEmailExtension.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=SETTINGS_REGISTRATION_TAG,
        summary='Listar politicas por tipo de usuario',
        description=(
            'Devuelve que politica de registro por dominio aplica para cada '
            'tipo de usuario configurado en el sistema.'
        ),
        responses={200: UserTypeWithOptionSerializerList(many=True)},
    )
)
class UserTypeOptionView(generics.ListAPIView):    
    """Lista la relación entre tipo de usuario y política de registro.

    Se deja publica porque otras pantallas pueden necesitar conocer la regla
    vigente antes de intentar un alta o una validación de dominio.
    """

    permission_classes = [AllowAny]
    serializer_class = UserTypeWithOptionSerializerList
    queryset = UserTypeWithOption.objects.all()


@extend_schema_view(
    put=extend_schema(
        tags=SETTINGS_REGISTRATION_TAG,
        summary='Actualizar politica de un tipo de usuario',
        description=(
            'Reasigna la opcion de registro por dominio para un tipo de usuario. '
            'Se usa para cambiar si un rol permite todos los dominios, solo los '
            'configurados o todos excepto los configurados.'
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Identificador del registro UserTypeWithOption. Internamente la vista lo recibe como `pk`.',
            )
        ],
        request=UserTypeOptionUpdateInputSerializer,
        responses={
            200: OpenApiResponse(description='Politica actualizada correctamente.'),
            400: OpenApiResponse(description='Payload invalido o tipo de usuario no encontrado.'),
        },
    ),
    patch=extend_schema(
        tags=SETTINGS_REGISTRATION_TAG,
        summary='Actualizar parcialmente politica de un tipo de usuario',
        description='Actualiza la opcion de registro asociada a un tipo de usuario.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Identificador del registro UserTypeWithOption. Internamente la vista lo recibe como `pk`.',
            )
        ],
        request=UserTypeOptionUpdateInputSerializer,
        responses={
            200: OpenApiResponse(description='Politica actualizada correctamente.'),
            400: OpenApiResponse(description='Payload invalido o tipo de usuario no encontrado.'),
        },
    ),
)
class UserTypeOptionUpdateView(generics.UpdateAPIView):
    """Actualiza la política de registro asociada a un tipo de usuario."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = UserTypeOptionUpdateInputSerializer
    queryset = UserTypeWithOption.objects.all()

    def update(self, request, *args, **kwargs):
        """Reasigna `option_register` para el registro identificado por `pk`."""

        pk = kwargs.get('pk')
        input_serializer = UserTypeOptionUpdateInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {'message': 'Error Update', 'code': 400, 'errors': input_serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        try:
            object_type_update = UserTypeWithOption.objects.get(pk=pk)
            object_type_update.option_register = input_serializer.validated_data['option_register']
            object_type_update.save()
            return Response({'message':'Update Successful','code':200}, status=HTTP_200_OK)
        except UserTypeWithOption.DoesNotExist:
            return Response({'message':'Error Update', 'code':400}, status=HTTP_400_BAD_REQUEST)
