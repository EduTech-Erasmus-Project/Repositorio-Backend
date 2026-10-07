"""Vistas del modulo `user`.

Este archivo concentra la mayor parte de los flujos operativos del dominio de
usuarios: registro por rol, activación por correo, login, cambio y reseteo de
contraseña, consulta y actualización de perfil, aprobación administrativa y
reportes. La implementación es heredada y mezcla endpoints públicos, de perfil
y administrativos en un mismo archivo; por eso la documentación prioriza
explicar responsabilidades, supuestos por rol y side effects como el envío de
correos.
"""

import json
import logging
import math
from webbrowser import get

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer

from applications.user.emailManager import SendMail, SendEmailCreateUser, SendEmailCreateUserCheck, SendEmailConfirm, \
    SendEmailCreateUserCheck_Expert, SendEmail_activation_email, SendEmailCreateUserCheck_Admin_to_Expert, \
    SendEmailAdminCreateUser
from applications.user.auth_cookies import (
    clear_auth_cookies,
    clear_csrf_cookie,
    enforce_csrf,
    get_refresh_token_from_request,
    set_auth_cookies,
    set_csrf_cookie,
)
from applications.user.utils import Util
from applications.helpers_functions.env_compat import (
    get_contact_email_recipient,
    get_contact_email_recipient_name,
    get_domain_host_roa,
    get_roa_instance_name,
    get_roa_public_url,
)
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework import serializers, viewsets
from rest_framework.generics import GenericAPIView, RetrieveAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny
from .serializers import ChangePasswordSerializer, MyTokenObtainPairSerializer, RequestPasswordResetEmailSerializer, \
    SetNewPasswordSerializer, StudentListSerializer, UpdateTecherCollaboratingExpertApproveedSerializer, \
    UpdateTecherCollaboratingExpertDisapprovedSerializer, UserListSerializers, UserUpdatePictureSerializer, \
    UserReportSerializer, AdminAprovedTeacherCollaboratingExpertWithOaSerializer
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.shortcuts import get_object_or_404
from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.preferences.models import Preferences
from applications.profession.models import Profession
from applications.settings.models import Email, EmailExtensionsTeacher, UserTypeWithOption, OptionRegisterEmailExtension
import urllib3
import re
from .models import (
    User,
    Student,
    Teacher,
    CollaboratingExpert,
    Administrator
)
from .serializers import (
    UserAdminSerializer,
    UserListSerializer,
    UserAdmiUpdatenSerializer,
    StudentCreateSerializer,
    TeacherCreateSerializer,
    RoleSerializer,
    GeneralUserListSerializer,
    UserLoginDataSerializer,
    UserUpdateSerializer,
    StudentUpdateSerializer,
    TeacherUpdateSerializer,
    CollaboratingExpertCreateSerializer,
    CollaboratingExpertUpdateSerializer,
    AdminDisaprovedTeacherCollaboratingExpertSerializer,
    AdminAprovedTeacherCollaboratingExpertSerializer,
    AdminStudentListSerializer,
    AdminUpdateStudentSerializer,
    AdminTeacherListSerializer,
    AdminUpdateStudentSerializer,
    AdminCollaboratingExpertListSerializer,
    AdminUpdateCollaboratingExpertSerializer,
    AdminAdministratorListSerializer,
    AdminUpdateAdministratorSerializer,
    OrcidValidationSerializer,
    EmailContacSerializer,
)
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED
)
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser, IsGeneralUser, IsStudentUser, \
    IsTeacherUser
from roabackend.settings import DOMAIN
import jwt
from rest_framework import generics
from datetime import datetime, timezone, timedelta
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls.base import reverse
import os
from unipath import Path
import environ
import threading

from ..address.models import Country, Province, City, University, Campus

# Instancias reutilizadas para los distintos correos transaccionales del
# módulo. Se inicializan una vez y luego se usan desde varios endpoints.
mail_create = SendEmailCreateUser()
mail_create_check = SendEmailCreateUserCheck()
mail_create_expert = SendEmailCreateUserCheck_Expert()
mail_create_check_expert = SendEmailCreateUserCheck_Admin_to_Expert()
mail_confirm_email = SendEmail_activation_email()
mail_account_not_active = SendEmailAdminCreateUser()

env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
# Este módulo también lee `.env` porque varios flujos heredados obtienen de ahí
# datos de entorno al momento de ejecutar correos y URLs.
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

logger = logging.getLogger(__name__)


USER_AUTH_TAG = ['User Auth']
USER_ACCOUNT_TAG = ['User Account']
USER_ADMIN_ACCOUNT_TAG = ['User Admin Accounts']
USER_ADMIN_APPROVAL_TAG = ['User Admin Approvals']
USER_ADMIN_LIST_TAG = ['User Admin Lists']
USER_VERIFICATION_TAG = ['User Verification']
USER_REPORT_TAG = ['User Reports']

USER_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador interno del usuario.',
)
USER_PK_PARAMETER = OpenApiParameter(
    name='pk',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador interno del usuario.',
)
USER_EMAIL_PARAMETER = OpenApiParameter(
    name='email',
    type=str,
    location=OpenApiParameter.PATH,
    description='Correo electronico usado para ubicar el usuario.',
)
USER_VERIFY_TOKEN_PARAMETER = OpenApiParameter(
    name='token',
    type=str,
    location=OpenApiParameter.PATH,
    description='Token de activacion o recuperacion enviado por correo.',
)
USER_UIDB64_PARAMETER = OpenApiParameter(
    name='uidb64',
    type=str,
    location=OpenApiParameter.PATH,
    description='Identificador de usuario codificado en base64 para recuperacion de contrasena.',
)
USER_MESSAGE_RESPONSE = inline_serializer(
    name='UserMessageResponse',
    fields={
        'message': serializers.CharField(required=False),
        'error': serializers.CharField(required=False),
        'email': serializers.CharField(required=False),
        'code': serializers.IntegerField(required=False),
        'status': serializers.CharField(required=False),
        'details': serializers.JSONField(required=False),
    },
)
USER_TOKEN_RESPONSE = inline_serializer(
    name='UserTokenResponse',
    fields={
        'access': serializers.CharField(),
        'refresh': serializers.CharField(),
    },
)
USER_TOKEN_REFRESH_REQUEST = inline_serializer(
    name='UserTokenRefreshRequest',
    fields={
        'refresh': serializers.CharField(),
    },
)
USER_TOKEN_REFRESH_RESPONSE = inline_serializer(
    name='UserTokenRefreshResponse',
    fields={
        'access': serializers.CharField(),
        'refresh': serializers.CharField(required=False),
    },
)
USER_TOKEN_VERIFY_REQUEST = inline_serializer(
    name='UserTokenVerifyRequest',
    fields={
        'token': serializers.CharField(),
    },
)
USER_SET_VERIFY_REQUEST = inline_serializer(
    name='UserSetVerifyRequest',
    fields={
        'email': serializers.EmailField(),
    },
)
USER_COUNT_RESPONSE = inline_serializer(
    name='UserCountResponse',
    fields={
        'total_student': serializers.IntegerField(),
        'total_teacher': serializers.IntegerField(),
    },
)
USER_TOTAL_ROLE_RESPONSE = inline_serializer(
    name='UserTotalRoleResponse',
    fields={
        'total_expert_approved': serializers.IntegerField(),
        'total_expert_disapproved': serializers.IntegerField(),
        'total_teacher_approved': serializers.IntegerField(),
        'total_teacher_disapproved': serializers.IntegerField(),
        'total_student': serializers.IntegerField(),
    },
)
USER_PASSWORD_RESET_RESPONSE = inline_serializer(
    name='UserPasswordResetResponse',
    fields={
        'message': serializers.CharField(),
        'token': serializers.CharField(required=False),
        'uidb64': serializers.CharField(required=False),
        'status': serializers.IntegerField(required=False),
    },
)
USER_PASSWORD_TOKEN_RESPONSE = inline_serializer(
    name='UserPasswordTokenResponse',
    fields={
        'success': serializers.BooleanField(required=False),
        'message': serializers.CharField(required=False),
        'uidb64': serializers.CharField(required=False),
        'token': serializers.CharField(required=False),
        'error': serializers.CharField(required=False),
    },
)
USER_REPORT_PARAMETERS = [
    OpenApiParameter('upload', str, OpenApiParameter.QUERY, description='Usa `upload` para docentes con OAs o `not_upload` para docentes sin OAs.'),
    OpenApiParameter('query', str, OpenApiParameter.QUERY, description='Busca por nombres, apellidos o correo exacto.'),
    OpenApiParameter('city', int, OpenApiParameter.QUERY, description='Filtra por ciudad del docente.'),
    OpenApiParameter('university', int, OpenApiParameter.QUERY, description='Filtra por universidad del docente.'),
    OpenApiParameter('campus', int, OpenApiParameter.QUERY, description='Filtra por campus del docente.'),
    OpenApiParameter('created_init', str, OpenApiParameter.QUERY, description='Fecha inicial de creacion en formato YYYY-MM-DD.'),
    OpenApiParameter('created_end', str, OpenApiParameter.QUERY, description='Fecha final de creacion en formato YYYY-MM-DD.'),
    OpenApiParameter('page', int, OpenApiParameter.QUERY, description='Numero de pagina a consultar.'),
    OpenApiParameter('page_size', int, OpenApiParameter.QUERY, description='Cantidad de resultados por pagina.'),
]


class UserReportPagination(PageNumberPagination):
    """Paginacion server-side para el endpoint administrativo de reportes."""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def filter_users_by_query_param(queryset, request):
    """Aplica busqueda opcional por nombre, apellido o correo antes de paginar."""

    query = request.query_params.get('query')
    if query is None:
        return queryset

    query = query.strip()
    if not query:
        return queryset

    return queryset.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )


@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_ACCOUNT_TAG,
        summary='Listar perfil administrador autenticado',
        description='Devuelve el perfil administrador asociado al usuario autenticado.',
        responses={200: UserListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_ACCOUNT_TAG,
        summary='Consultar administrador autenticado',
        description='Recupera el detalle del administrador solo si el identificador de la ruta corresponde al usuario autenticado.',
        parameters=[USER_ID_PARAMETER],
        responses={200: UserListSerializer, 404: USER_MESSAGE_RESPONSE},
    ),
    create=extend_schema(
        tags=USER_ADMIN_ACCOUNT_TAG,
        summary='Crear usuario administrador',
        description='Crea una cuenta con perfil administrador y la deja activa para operar en el sistema.',
        request=UserAdminSerializer,
        responses={200: UserListSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_ACCOUNT_TAG,
        summary='Actualizar perfil administrador',
        description='Actualiza nombres y datos del perfil administrador del usuario autenticado.',
        parameters=[USER_ID_PARAMETER],
        request=UserAdmiUpdatenSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.'), 404: USER_MESSAGE_RESPONSE},
    ),
    destroy=extend_schema(
        tags=USER_ADMIN_ACCOUNT_TAG,
        summary='Eliminar administrador no disponible',
        description='Operacion conservada por compatibilidad; la vista responde que el API no esta disponible.',
        parameters=[USER_ID_PARAMETER],
        responses={404: USER_MESSAGE_RESPONSE},
    ),
)
class UserAdminView(viewsets.ViewSet):
    """CRUD acotado del perfil administrativo autenticado."""

    permission_classes = [IsAuthenticated, IsAdministratorUser, ]
    serializer_class = UserListSerializer

    def create(self, request, *args, **kwargs):
        """Crea una nueva cuenta con perfil de administrador."""
        
        serializer = UserAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_admin = Administrator.objects.create(
            country=serializer.validated_data['country'],
            city=serializer.validated_data['city'],
            phone=serializer.validated_data['phone'],
            observation=serializer.validated_data['observation'],
        )
        new_admin.is_active = True
        new_admin.save()
        new_user = User.objects.create_admin_user(
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        new_user.administrator = new_admin
        new_user.save()
        serializer = UserListSerializer(new_user)
        return Response(serializer.data, status=HTTP_200_OK)

    def list(self, request):
        """Lista el registro administrativo asociado al usuario autenticado."""

        queryset = User.objects.filter(email=self.request.user.email)
        serializer = UserListSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera el detalle del administrador autenticado por su propio `pk`."""
        
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter().order_by('-pk')
            user = get_object_or_404(queryset, pk=pk)
            serializer = UserListSerializer(user)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def update(self, request, pk=None, project_pk=None):
        """Actualiza el perfil del administrador autenticado por su propio `pk`."""
        
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter(administrator__is_active=True).order_by('-pk')
            instance = get_object_or_404(queryset, pk=pk)
            instance_admin = Administrator.objects.get(pk=instance.administrator.id)
            serializer = UserAdmiUpdatenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.first_name = serializer.validated_data['first_name']
            instance.last_name = serializer.validated_data['last_name']
            instance_admin.country = serializer.validated_data['country']
            instance_admin.city = serializer.validated_data['city']
            instance_admin.phone = serializer.validated_data['phone']
            instance_admin.is_active = serializer.validated_data['is_active']
            instance_admin.observation = serializer.validated_data['observation']
            instance.save()
            instance_admin.save()
            return Response({"message": "success"}, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """Operación no expuesta para administradores desde este viewset."""
        
        return Response({"message": "Api not found"}, status=HTTP_404_NOT_FOUND)




@extend_schema_view(
    list=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Consultar usuario autenticado',
        description='Devuelve el perfil general del usuario autenticado con roles activos y datos relacionados.',
        responses={200: GeneralUserListSerializer, 404: USER_MESSAGE_RESPONSE},
    ),
    retrieve=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Consultar usuario por id propio',
        description='Recupera el perfil general solo cuando el `id` de la ruta coincide con el usuario autenticado.',
        parameters=[USER_ID_PARAMETER],
        responses={200: GeneralUserListSerializer, 404: USER_MESSAGE_RESPONSE},
    ),
    create=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Registrar usuario por roles',
        description=(
            'Crea una cuenta general con uno de los roles operativos: estudiante, docente o experto. '
            'El payload incluye campos comunes del usuario y campos especificos segun el rol solicitado.'
        ),
        request=RoleSerializer,
        responses={200: GeneralUserListSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Actualizar usuario autenticado',
        description=(
            'Actualiza datos comunes y, segun `roles`, actualiza o crea el perfil de estudiante, docente o experto. '
            'Solo se permite actualizar el usuario autenticado.'
        ),
        parameters=[USER_ID_PARAMETER],
        request=UserUpdateSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.'), 404: USER_MESSAGE_RESPONSE},
    ),
    destroy=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Desactivar rol de usuario',
        description='No elimina fisicamente la cuenta; marca como inactivo el perfil indicado en `roles`.',
        parameters=[USER_ID_PARAMETER],
        request=UserUpdateSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class ManagementUserView(viewsets.ViewSet):
    """Registro y mantenimiento del perfil general para student/teacher/expert.

    El flujo crea primero el perfil específico del rol y luego lo enlaza con la
    cuenta `User`. En el caso de docente, además persiste ciudad,
    universidad y campus en el modelo principal porque forman parte del
    contrato histórico de ese rol.
    """
    serializer_class = GeneralUserListSerializer

    def get_permissions(self):
        """Permite registro público y exige autenticación para el resto."""

        if (self.action == 'create'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsGeneralUser, ]
        return [permission() for permission in permission_classes]

    def asing_array_filter_only_all(self, emails_extension,email_string, option_value):
        """Evalúa si un correo pasa la política `ONLY`, `EXCEPT` o `ALL`."""

        emails_domain = []
        for email in emails_extension:
            emails_domain = email.domain
        email_split = email_string.split('@')
        if option_value == 'ONLY':
            if email_split[-1] in emails_domain:
                return True
            else:
                return False
        elif option_value == 'EXCEPT':
            if email_split[-1] in emails_domain:
                return False
            else:
                return True
        elif option_value == "ALL":
            return True

    def checkEmail(self, email_string):
        """Valida el dominio permitido para altas de teacher/expert."""

        typeRolExtension = UserTypeWithOption.objects.get(description='TEACHER')
        option_register = OptionRegisterEmailExtension.objects.get(id=typeRolExtension.option_register.id)

        emails_extension = None
        if option_register.type_option == 'EXCEPT':
            emails_extension = EmailExtensionsTeacher.objects.filter(option_register_email=typeRolExtension.option_register.id,is_active=True)
            return  self.asing_array_filter_only_all(emails_extension, email_string, 'EXCEPT')
        elif option_register.type_option == 'ONLY':
            emails_extension = EmailExtensionsTeacher.objects.filter(option_register_email=typeRolExtension.option_register.id, is_active=True)
            return self.asing_array_filter_only_all(emails_extension,email_string, 'ONLY')

        else:
            emails_extension = EmailExtensionsTeacher.objects.filter(is_active=True)
            return self.asing_array_filter_only_all(emails_extension, email_string, 'ALL')

    def _get_required_location_objects(self, data):
        """Valida y resuelve ubicacion academica para registros teacher/expert."""

        required_fields = ("city", "university", "campus")
        missing_fields = {
            field: ["Este campo es requerido para docentes y expertos."]
            for field in required_fields
            if data.get(field) in (None, "")
        }
        if missing_fields:
            raise serializers.ValidationError(missing_fields)

        country_obj = Country.objects.filter(province__city__id=data.get("city")).first()
        province_obj = Province.objects.filter(city__id=data.get("city")).first()
        city_obj = City.objects.filter(id=data.get("city")).first()
        university_obj = University.objects.filter(id=data.get("university")).first()
        campus_obj = Campus.objects.filter(id=data.get("campus")).first()

        invalid_fields = {}
        if country_obj is None or province_obj is None or city_obj is None:
            invalid_fields["city"] = ["Ciudad invalida."]
        if university_obj is None:
            invalid_fields["university"] = ["Universidad invalida."]
        if campus_obj is None:
            invalid_fields["campus"] = ["Campus invalido."]
        elif campus_obj.university_id != university_obj.id:
            invalid_fields["campus"] = ["El campus no pertenece a la universidad seleccionada."]
        elif campus_obj.city_id is not None and campus_obj.city_id != city_obj.id:
            invalid_fields["campus"] = ["El campus no pertenece a la ciudad seleccionada."]
        if invalid_fields:
            raise serializers.ValidationError(invalid_fields)

        return country_obj, province_obj, city_obj, university_obj, campus_obj

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
            Servicio para crear un nuevo usuario (Estudiante, Docente, Experto Colaborador).
        """

        dataRes = request.data

        role_serializer = RoleSerializer(data=request.data)
        role_serializer.is_valid(raise_exception=True)
        new_student = Student()
        new_teacher = Teacher()
        new_expert = CollaboratingExpert()
        location_objects = None

        if role_serializer.validated_data['roles'][0] in ('teacher', 'expert'):
            location_objects = self._get_required_location_objects(dataRes)

        for role in role_serializer.validated_data['roles']:

            if role == 'student' and role != 'teacher' and role != 'expert':
                serializer = StudentCreateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_student = Student.objects.create(
                    birthday=serializer.validated_data['birthday'],
                    has_disability=serializer.validated_data['has_disability'],
                    disability_description=serializer.validated_data['disability_description'],
                )
                education_levels = EducationLevel.objects.filter(
                    id__in=serializer.validated_data['education_levels']
                )
                knowledge_areas = KnowledgeArea.objects.filter(
                    id__in=serializer.validated_data['knowledge_areas']
                )
                preferences = Preferences.objects.filter(
                    id__in=serializer.validated_data['preferences']
                )
                for education_level in education_levels:
                    new_student.education_levels.add(education_level)
                for knowledge_area in knowledge_areas:
                    new_student.knowledge_areas.add(knowledge_area)
                for preference in preferences:
                    new_student.preferences.add(preference)

                value_active = True
                new_student.is_active = value_active

                if serializer.validated_data['has_disability'] is False:
                    self.set_email_conform(new_student.id, request, "student")


                else:
                    new_student.is_account_active = True
                    mail_create.sendMailCreate(request.data['email'], request.data['first_name'])

                new_student.save()

            if role == 'teacher' and role != 'student' and role != 'expert':
                teacher_serializer = TeacherCreateSerializer(data=request.data)
                teacher_serializer.is_valid(raise_exception=True)
                if not self.checkEmail(request.data['email']):
                    value_active = False
                    name_user_account = role_serializer.validated_data['first_name'] + " " + \
                                        role_serializer.validated_data['last_name']
                    # Logica heredada: antes se buscaban usuarios `is_superuser=True`
                    # y se enviaba la notificacion de revision a cada uno.
                    # Se conserva documentada por trazabilidad del flujo, pero la
                    # regla vigente notifica a administradores activos y al
                    # buzon institucional, sin incluir superusuarios.
                    #
                    # users_admin = User.objects.filter(is_superuser=True)
                    # for user_admin in users_admin:
                    #     user_email = user_admin.email
                    #     user_name = user_admin.first_name + " " + user_admin.last_name
                    #     mail_account_not_active.sendMail_validate_account_teacher_Admin(
                    #         user_email,
                    #         user_name,
                    #         name_user_account,
                    #     )
                    for recipient_email, recipient_name in get_user_admin_notification_recipients():
                        mail_account_not_active.sendMail_validate_account_teacher_Admin(
                            recipient_email,
                            recipient_name,
                            name_user_account,
                        )
                else:
                    value_active = True

                new_teacher = Teacher.objects.create(
                    is_active=value_active,
                )

                professions = Profession.objects.filter(
                    id__in=teacher_serializer.validated_data['professions']
                )
                for profession in professions:
                    new_teacher.professions.add(profession)

                self.set_email_conform(new_teacher.id, request, "teacher")
                new_teacher.save()

            if role == 'expert' and role != 'teacher' and role != 'student':
                serializer = CollaboratingExpertCreateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                if not self.checkEmail(request.data['email']):
                    value_active = False
                    name_user_account = role_serializer.validated_data['first_name'] + " " + \
                                        role_serializer.validated_data['last_name']
                    # Logica heredada: antes se buscaban usuarios `is_superuser=True`
                    # y se enviaba la notificacion de revision a cada uno.
                    # Se conserva documentada por trazabilidad del flujo, pero la
                    # regla vigente notifica a administradores activos y al
                    # buzon institucional, sin incluir superusuarios.
                    #
                    # users_admin = User.objects.filter(is_superuser=True)
                    # for user_admin in users_admin:
                    #     user_email = user_admin.email
                    #     user_name = user_admin.first_name + " " + user_admin.last_name
                    #     mail_account_not_active.sendMail_validate_account_expert_Admin(
                    #         user_email,
                    #         user_name,
                    #         name_user_account,
                    #     )
                    for recipient_email, recipient_name in get_user_admin_notification_recipients():
                        mail_account_not_active.sendMail_validate_account_expert_Admin(
                            recipient_email,
                            recipient_name,
                            name_user_account,
                        )
                else:
                    value_active = True

                new_expert = CollaboratingExpert.objects.create(
                    expert_level=serializer.validated_data['expert_level'],
                    web=serializer.validated_data['web'],
                    academic_profile=serializer.validated_data['academic_profile'],
                    is_active=value_active,
                )
                self.set_email_conform(new_expert.id, request, "expert")
                new_expert.save()

        # Para docentes, el alta históricamente deriva país y provincia a
        # partir de la ciudad enviada en el payload.

        new_user = User.objects.create_general_user(
            first_name=role_serializer.validated_data['first_name'],
            last_name=role_serializer.validated_data['last_name'],
            email=role_serializer.validated_data['email'],
            password=role_serializer.validated_data['password'],
        )


        new_user.image = role_serializer.validated_data['image']
        if new_student.pk is not None:
            new_user.student = new_student
            new_user.save()
        if new_teacher.pk is not None:
            countryObj, provinceObj, cityObj, universityObj, campusObj = location_objects

            new_user.teacher = new_teacher
            new_user.country = countryObj
            new_user.province = provinceObj
            new_user.city = cityObj
            new_user.university = universityObj
            new_user.campus = campusObj
            new_user.save()
        if new_expert.pk is not None:
            countryObj, provinceObj, cityObj, universityObj, campusObj = location_objects

            new_user.collaboratingExpert = new_expert
            new_user.country = countryObj
            new_user.province = provinceObj
            new_user.city = cityObj
            new_user.university = universityObj
            new_user.campus = campusObj
            new_user.save()
        serializer = GeneralUserListSerializer(new_user)
        return Response(serializer.data, status=HTTP_200_OK)

    def set_email_conform(self, id_user, request, role):
        """Envía el enlace de activación con un JWT efímero del rol indicado."""

        token = jwt.encode({"id": id_user, "role": role, "exp": datetime.now(tz=timezone.utc) + timedelta(hours=24)},
                           "secreto", algorithm="HS256")
        try:

            mail_confirm_email.send_email_confirm_email(request.data['email'], request.data['first_name'], token)
        except Exception as e:
            logger.exception("Error enviando correo de confirmación para el usuario %s", id_user)

    def list(self, request):
        """
            Servicio para listar el usuario autenticado (Estudiante, Docente, Experto Colaborador).
        """
        user = self.request.user
        if int(request.user.id) == int(user.pk):
            queryset = User.objects.filter(
                Q(student__is_active=True) | Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
            )
            user = get_object_or_404(queryset, pk=user.pk)
            serializer = GeneralUserListSerializer(user)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar el usuario autenticado (Estudiante, Docente, Experto Colaborador).
        """
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter(
                Q(student__is_active=True) | Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
            )
            user = get_object_or_404(queryset, pk=pk)
            serializer = GeneralUserListSerializer(user)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar el usuario se necesita estar autenticado como (Estudiante, Docente, Experto Colaborador).
        """
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter(
                Q(student__is_active=True) | Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
            )

            instance = get_object_or_404(queryset, pk=pk)
            user_serializer = UserUpdateSerializer(data=request.data)
            user_serializer.is_valid(raise_exception=True)
            instance.first_name = user_serializer.validated_data['first_name']
            instance.last_name = user_serializer.validated_data['last_name']
            if user_serializer.validated_data.get('city') is not None:
                instance.city_id = user_serializer.validated_data['city']
            if user_serializer.validated_data.get('university') is not None:
                instance.university_id = user_serializer.validated_data['university']
            if user_serializer.validated_data.get('campus') is not None:
                instance.campus_id = user_serializer.validated_data['campus']

            for role in user_serializer.validated_data['roles']:
                if instance.student is not None and role == 'student':
                    serializer = StudentUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    student_instance = Student.objects.get(pk=instance.student.id)
                    student_instance.birthday = serializer.validated_data['birthday']
                    student_instance.has_disability = serializer.validated_data['has_disability']
                    student_instance.disability_description = serializer.validated_data['disability_description']

                    education_levels = EducationLevel.objects.filter(
                        id__in=serializer.validated_data['education_levels']
                    )
                    knowledge_areas = KnowledgeArea.objects.filter(
                        id__in=serializer.validated_data['knowledge_areas']
                    )
                    preferences = Preferences.objects.filter(
                        id__in=serializer.validated_data['preferences']
                    )
                    student_instance.education_levels.clear()
                    student_instance.knowledge_areas.clear()
                    student_instance.preferences.clear()
                    for education_level in education_levels:
                        student_instance.education_levels.add(education_level)
                    for knowledge_area in knowledge_areas:
                        student_instance.knowledge_areas.add(knowledge_area)
                    for preference in preferences:
                        student_instance.preferences.add(preference)
                    student_instance.save()

                if instance.student is None and role == "student":
                    serializer = StudentUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    new_student = Student.objects.create(
                        birthday=serializer.validated_data['birthday'],
                        has_disability=serializer.validated_data['has_disability'],
                        disability_description=serializer.validated_data['disability_description'],
                    )
                    education_levels = EducationLevel.objects.filter(
                        id__in=serializer.validated_data['education_levels']
                    )
                    knowledge_areas = KnowledgeArea.objects.filter(
                        id__in=serializer.validated_data['knowledge_areas']
                    )
                    preferences = Preferences.objects.filter(
                        id__in=serializer.validated_data['preferences']
                    )
                    for education_level in education_levels:
                        new_student.education_levels.add(education_level)
                    for knowledge_area in knowledge_areas:
                        new_student.knowledge_areas.add(knowledge_area)
                    for preference in preferences:
                        new_student.preferences.add(preference)
                    new_student.save()
                    instance.student = new_student

                if instance.teacher is not None and role == 'teacher':
                    serializer = TeacherUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    teacher_instance = Teacher.objects.get(pk=instance.teacher.id)
                    professions = Profession.objects.filter(
                        id__in=serializer.validated_data['professions']
                    )
                    teacher_instance.professions.clear()
                    for profession in professions:
                        teacher_instance.professions.add(profession)
                    teacher_instance.save()

                if instance.teacher is None and role == "teacher":
                    serializer = TeacherUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    new_teacher = Teacher.objects.create(
                        is_active=False
                    )
                    professions = Profession.objects.filter(
                        id__in=serializer.validated_data['professions']
                    )
                    for profession in professions:
                        new_teacher.professions.add(profession)
                    new_teacher.save()
                    instance.teacher = new_teacher

                if instance.collaboratingExpert is not None and role == 'expert':
                    serializer = CollaboratingExpertUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    collaboratingExpert_instance = CollaboratingExpert.objects.get(pk=instance.collaboratingExpert.id)

                    collaboratingExpert_instance.expert_level = serializer.validated_data['expert_level']
                    collaboratingExpert_instance.web = serializer.validated_data['web']
                    collaboratingExpert_instance.academic_profile = serializer.validated_data['academic_profile']
                    collaboratingExpert_instance.save()

                if instance.collaboratingExpert is None and role == 'expert':
                    serializer = CollaboratingExpertUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    new_expert = CollaboratingExpert.objects.create(
                        expert_level=serializer.validated_data['expert_level'],
                        web=serializer.validated_data['web'],
                        academic_profile=serializer.validated_data['academic_profile'],
                    )
                    new_expert.save()
                    instance.collaboratingExpert = new_expert
            instance.save()
            serializer = GeneralUserListSerializer(instance)
            return Response({"message": "success update"}, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """
            Servicio para eliminar el usuario se necesita estar autenticado como (Estudiante, Docente, Experto Colaborador).
        """
        instance = User.objects.get(pk=pk)
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for role in serializer.validated_data['roles']:
            if instance.student is not None and role == 'student':
                student = get_object_or_404(Student, id=instance.student.id)
                student.is_active = False
                student.save()

            if instance.teacher is not None and role == 'teacher':
                teacher = get_object_or_404(Teacher, id=instance.teacher.id)
                teacher.is_active = False
                teacher.save()

            if instance.collaboratingExpert is not None and role == 'expert':
                collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
                collaboratingExpert.is_active = False
                collaboratingExpert.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


@extend_schema_view(
    post=extend_schema(
        tags=USER_VERIFICATION_TAG,
        summary='Reenviar enlace de verificacion',
        description='Genera un nuevo token de activacion para una cuenta registrada y envia el enlace por correo.',
        request=USER_SET_VERIFY_REQUEST,
        responses={200: USER_MESSAGE_RESPONSE, 400: USER_MESSAGE_RESPONSE},
    )
)
class set_new_token_verify(APIView):
    """Reemite el enlace de verificación de correo para cuentas pendientes."""

    permission_classes = []
    serializer_class = serializers.Serializer

    def post(self, request):
        try:
            user = get_object_or_404(User, email=request.data['email'])
        except:
            return Response({"message": "Correo no registrado", "status": 400}, status=HTTP_400_BAD_REQUEST)
        if user:
            user_role, user_id = self.role(user)
            self.set_email_conform_new_token(user_id, request.data['email'], user.first_name, user_role)
            return Response({"message": "Nuevo enlace creado", "status": 200}, status=HTTP_200_OK)
        else:
            return Response({"message": "Correo no registrado", "status": 400}, status=HTTP_400_BAD_REQUEST)

    def role(self, user):
        """Resuelve el rol operativo principal usado por la verificación."""

        if user.collaboratingExpert_id is not None:
            return 'expert', user.collaboratingExpert_id
        elif user.student_id is not None:
            return 'student', user.student_id
        elif user.teacher_id is not None:
            return 'teacher', user.teacher_id

    def set_email_conform_new_token(self, id_user, email_user, name_user, role):
        """Genera y envía un nuevo token de activación para el rol indicado."""

        token = jwt.encode({"id": id_user, "role": role, "exp": datetime.now(tz=timezone.utc) + timedelta(hours=24)},
                           "secreto", algorithm="HS256")
        mail_confirm_email.send_email_confirm_email(email_user, name_user,
                                                    token)


@extend_schema_view(
    get=extend_schema(
        tags=USER_VERIFICATION_TAG,
        summary='Verificar correo y activar cuenta',
        description=(
            'Valida el token enviado por correo, activa la cuenta del rol indicado y dispara correos posteriores '
            'segun si el usuario queda aprobado o pendiente de revision administrativa.'
        ),
        parameters=[USER_VERIFY_TOKEN_PARAMETER, USER_EMAIL_PARAMETER],
        responses={200: USER_MESSAGE_RESPONSE, 400: USER_MESSAGE_RESPONSE},
    )
)
class VerifyEmail(generics.GenericAPIView):
    """Activa la cuenta a partir del token enviado por correo.

    Además de marcar `is_account_active`, este flujo dispara correos
    posteriores según el estado de aprobación del rol.
    """

    permission_classes = []
    serializer_class = serializers.Serializer

    def get(self, request, token, email):
        try:
            payload = jwt.decode(token, "secreto", algorithms=["HS256"])
            role = payload['role']
            id = payload['id']
            if role == 'student':
                try:
                    student = Student.objects.get(pk=id);
                    user = User.objects.get(student_id=student.id);
                    if student.is_account_active is True:
                        return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                except:
                    return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                student.is_account_active = True
                mail_create.sendMailCreate(user.email, user.first_name)
                student.save()
                return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)
            if role == 'teacher':
                try:
                    teacher = Teacher.objects.get(pk=id);
                    user = User.objects.get(teacher_id=teacher.id);
                    if teacher.is_account_active is True:
                        return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                    teacher.is_account_active = True
                except:
                    return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)

                if teacher.is_active is False:
                    mail_create_check.sendMailCreateCheckAdmin(user.email, user.first_name)
                else:
                    mail_create.sendMailCreate(user.email, user.first_name)
                teacher.save()
                return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)
            if role == 'expert':
                try:
                    expert = CollaboratingExpert.objects.get(pk=id);
                    user = User.objects.get(collaboratingExpert_id=expert.id);
                    if expert.is_account_active is True:
                        return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                except:
                    return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                expert.is_account_active = True
                if expert.is_active is False:
                    mail_create_check_expert.sendMailCreate_Admin_to_Expert(user.email, user.first_name)
                else:
                    mail_create_expert.sendMailCreate_Expert(user.email, user.first_name)
                expert.save()
                return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)

        except jwt.ExpiredSignatureError as identifier:
            return Response({'error': 'Activacion expirada'}, status=HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError as error:
            return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)


mail_aproved = SendEmailConfirm()
CONTACT_EMAIL_RECIPIENT = get_contact_email_recipient()
CONTACT_EMAIL_RECIPIENT_NAME = get_contact_email_recipient_name()
CONTACT_ROA_INSTANCE_NAME = get_roa_instance_name()
CONTACT_ROA_PUBLIC_URL = get_roa_public_url()


def get_user_admin_notification_recipients():
    """Devuelve administradores activos y el buzon institucional sin duplicados."""

    recipients = []
    seen_emails = set()
    active_administrators = User.objects.filter(administrator__is_active=True).order_by('id')

    for admin_user in active_administrators:
        email = (admin_user.email or '').strip()
        if not email:
            continue
        normalized_email = email.lower()
        if normalized_email in seen_emails:
            continue
        full_name = f"{admin_user.first_name} {admin_user.last_name}".strip() or "Administrador ROA"
        recipients.append((email, full_name))
        seen_emails.add(normalized_email)

    institutional_email = CONTACT_EMAIL_RECIPIENT.strip()
    if institutional_email:
        normalized_institutional_email = institutional_email.lower()
        if normalized_institutional_email not in seen_emails:
            recipients.append((CONTACT_EMAIL_RECIPIENT, CONTACT_EMAIL_RECIPIENT_NAME))

    return recipients


def roleUser(user):
    """Devuelve el rol principal y el id del perfil asociado al usuario."""

    if user.collaboratingExpert_id is not None:
        return 'expert', user.collaboratingExpert_id
    elif user.student_id is not None:
        return 'student', user.student_id
    elif user.teacher_id is not None:
        return 'teacher', user.teacher_id


@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Listar docentes pendientes de aprobacion',
        description='Lista usuarios con perfil docente que todavia no estan aprobados administrativamente.',
        responses={200: AdminDisaprovedTeacherCollaboratingExpertSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Consultar docente pendiente',
        description='Devuelve el detalle administrativo de un docente pendiente o desaprobado.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminDisaprovedTeacherCollaboratingExpertSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Aprobar o actualizar docente pendiente',
        description='Actualiza el estado `teacher_is_active` del docente pendiente y envia correo de confirmacion si corresponde.',
        parameters=[USER_ID_PARAMETER],
        request=UpdateTecherCollaboratingExpertDisapprovedSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminDisaprovedTeacher(viewsets.ViewSet):
    """Gestiona docentes pendientes o desaprobados para administración."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminDisaprovedTeacherCollaboratingExpertSerializer
    def list(self, request):
        """
            Servicio para listar Docentes no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(teacher__is_active=False)
        queryset = filter_users_by_query_param(queryset, request)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
            return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Docentes no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Docentes no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertDisapprovedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None and instance.teacher.is_active is False:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            mail_aproved.sendEmailConfirmAdmin(instance.email, instance.first_name);
            teacher.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message
@extend_schema_view(
    delete=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Eliminar docente pendiente',
        description='Elimina la cuenta `User` y el perfil `Teacher` asociado cuando el docente pendiente es rechazado.',
        parameters=[USER_ID_PARAMETER],
        responses={200: USER_MESSAGE_RESPONSE, 400: USER_MESSAGE_RESPONSE},
    )
)
class AdminDisaprovedTeacherDelete(DestroyAPIView):
    """Elimina un registro docente pendiente junto con su cuenta `User`."""

    permission_classes =  [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminDisaprovedTeacherCollaboratingExpertSerializer
    queryset = User.objects.all()
    def delete(self, request, pk=None):
        """
            Servicio para eliminar el usuario existente
        """
        try:
            user = User.objects.get(id=pk)
            user_teacher = Teacher.objects.get(pk=user.teacher_id)
            user.delete()
            user_teacher.delete()
            return Response({'message': 'User deleted successfully', 'code':200}, status= HTTP_200_OK)
        except Exception as e :
            logger.exception("Error eliminando docente desaprobado con id %s", pk)
            return Response({'message':'Error deleting record from database', 'code':400}, status= HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Listar expertos pendientes de aprobacion',
        description='Lista usuarios con perfil de experto colaborador que todavia no estan aprobados administrativamente.',
        responses={200: AdminDisaprovedTeacherCollaboratingExpertSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Consultar experto pendiente',
        description='Devuelve el detalle administrativo de un experto colaborador pendiente o desaprobado.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminDisaprovedTeacherCollaboratingExpertSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Aprobar o actualizar experto pendiente',
        description='Actualiza el estado `expert_is_active` del experto pendiente y envia correo de confirmacion si corresponde.',
        parameters=[USER_ID_PARAMETER],
        request=UpdateTecherCollaboratingExpertDisapprovedSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminDisaprovedCollaboratingExpert(viewsets.ViewSet):
    """Gestiona expertos pendientes o desaprobados para administración."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminDisaprovedTeacherCollaboratingExpertSerializer

    def list(self, request):
        """
            Servicio para listar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(collaboratingExpert__is_active=False)
        queryset = filter_users_by_query_param(queryset, request)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
            return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Experto Colaborador no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertDisapprovedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.collaboratingExpert is not None and instance.collaboratingExpert.is_active is False:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            mail_aproved.sendEmailConfirmAdmin(instance.email, instance.first_name);
            collaboratingExpert.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message

@extend_schema_view(
    delete=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Eliminar experto pendiente',
        description='Elimina la cuenta `User` y el perfil `CollaboratingExpert` asociado cuando el experto pendiente es rechazado.',
        parameters=[USER_ID_PARAMETER],
        responses={200: USER_MESSAGE_RESPONSE, 400: USER_MESSAGE_RESPONSE},
    )
)
class AdminDisaprovedCollaboratingExpertDelete(DestroyAPIView):
    """Elimina un experto pendiente junto con su cuenta `User`."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminDisaprovedTeacherCollaboratingExpertSerializer
    queryset = User.objects.all()
    def delete(self, request, pk=None):
        """
            Eliminar usuario de tipo Experto Colaborador
        """
        try:
            user = User.objects.get(pk=pk)
            user_collaborating_expert = CollaboratingExpert.objects.get(pk =user.collaboratingExpert_id)
            user.delete()
            user_collaborating_expert.delete()
            return Response({'message':'User deleted successfully', 'code':200}, status= HTTP_200_OK)
        except Exception as e:
            logger.exception("Error eliminando experto desaprobado con id %s", pk)
            return Response({'message':'Error to delete User', 'code':400}, status=HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Listar docentes aprobados',
        description='Lista usuarios con perfil docente activo/aprobado.',
        responses={200: AdminAprovedTeacherCollaboratingExpertSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Consultar docente aprobado',
        description='Devuelve el detalle de un docente aprobado, incluyendo OAs creados cuando aplica.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminAprovedTeacherCollaboratingExpertWithOaSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Actualizar estado de docente aprobado',
        description='Permite desactivar o mantener activo un perfil docente ya aprobado.',
        parameters=[USER_ID_PARAMETER],
        request=UpdateTecherCollaboratingExpertApproveedSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminAprovedTeacher(viewsets.ViewSet):
    """Gestiona docentes ya aprobados desde la interfaz administrativa."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminAprovedTeacherCollaboratingExpertSerializer

    def list(self, request):
        """
            Servicio para listar Docente no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(teacher__is_active=True)
        queryset = filter_users_by_query_param(queryset, request)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Docente no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(teacher__is_active=True)
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminAprovedTeacherCollaboratingExpertWithOaSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Docente no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertApproveedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None and instance.teacher.is_active is True:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            teacher.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Listar expertos aprobados',
        description='Lista usuarios con perfil experto colaborador activo/aprobado.',
        responses={200: AdminAprovedTeacherCollaboratingExpertSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Consultar experto aprobado',
        description='Devuelve el detalle administrativo de un experto colaborador aprobado.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminAprovedTeacherCollaboratingExpertSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_APPROVAL_TAG,
        summary='Actualizar estado de experto aprobado',
        description='Permite desactivar o mantener activo un perfil experto ya aprobado.',
        parameters=[USER_ID_PARAMETER],
        request=UpdateTecherCollaboratingExpertApproveedSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminAprovedCollaboratingExpert(viewsets.ViewSet):
    """Gestiona expertos ya aprobados desde la interfaz administrativa."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminAprovedTeacherCollaboratingExpertSerializer

    def list(self, request):
        """
            Servicio para listar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(collaboratingExpert__is_active=True)
        queryset = filter_users_by_query_param(queryset, request)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Experto Colaborador no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(collaboratingExpert__is_active=True)
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminAprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertApproveedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.collaboratingExpert is not None and instance.collaboratingExpert.is_active is True:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            collaboratingExpert.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Listar estudiantes para administracion',
        description='Lista todos los usuarios que tienen perfil estudiante.',
        responses={200: AdminStudentListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Consultar estudiante para administracion',
        description='Devuelve el detalle administrativo de un estudiante por id de usuario.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminStudentListSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Actualizar estado de estudiante',
        description='Activa o desactiva el perfil estudiante asociado al usuario.',
        parameters=[USER_ID_PARAMETER],
        request=AdminUpdateStudentSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminListStudent(viewsets.ViewSet):
    """Listado administrativo de usuarios con perfil estudiante."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminStudentListSerializer

    def list(self, request):
        """
            Servicio para listar estudiantes. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(student__isnull=False)
        )
        queryset = filter_users_by_query_param(queryset, request)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminStudentListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminStudentListSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar estudiantes por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(student__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminStudentListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar registro de un estudiante. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.student is not None:
            student = get_object_or_404(Student, id=instance.student.id)
            student.is_active = serializer.validated_data['student_is_active']
            student.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Listar docentes para administracion',
        description='Lista todos los usuarios que tienen perfil docente.',
        responses={200: AdminTeacherListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Consultar docente para administracion',
        description='Devuelve el detalle administrativo de un docente por id de usuario.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminTeacherListSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Actualizar estado de docente',
        description='Activa o desactiva el perfil docente asociado al usuario.',
        parameters=[USER_ID_PARAMETER],
        request=UpdateTecherCollaboratingExpertApproveedSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminListTeacher(viewsets.ViewSet):
    """Listado administrativo de usuarios con perfil docente."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminTeacherListSerializer

    def list(self, request):
        """
            Servicio para listar Docentes. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(teacher__isnull=False)
        ).order_by('-pk')
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminTeacherListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminTeacherListSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Docentes. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(teacher__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminTeacherListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Docente. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            teacher.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Listar expertos para administracion',
        description='Lista todos los usuarios que tienen perfil experto colaborador.',
        responses={200: AdminCollaboratingExpertListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Consultar experto para administracion',
        description='Devuelve el detalle administrativo de un experto colaborador por id de usuario.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminCollaboratingExpertListSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Actualizar estado de experto',
        description='Activa o desactiva el perfil experto colaborador asociado al usuario.',
        parameters=[USER_ID_PARAMETER],
        request=AdminUpdateCollaboratingExpertSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminListCollaboratingExpert(viewsets.ViewSet):
    """Listado administrativo de usuarios con perfil experto colaborador."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminCollaboratingExpertListSerializer

    def list(self, request):
        """
            Servicio para listar Expertos Colaboradores. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(collaboratingExpert__isnull=False)
        ).order_by('-pk')
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminCollaboratingExpertListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminCollaboratingExpertListSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Experto Colaborador por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(collaboratingExpert__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminCollaboratingExpertListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Experto Colaborador. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateCollaboratingExpertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.collaboratingExpert is not None:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            collaboratingExpert.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


@extend_schema_view(
    list=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Listar administradores',
        description='Lista usuarios administradores excluyendo al administrador autenticado.',
        responses={200: AdminAdministratorListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Consultar administrador',
        description='Devuelve el detalle administrativo de otro usuario administrador.',
        parameters=[USER_ID_PARAMETER],
        responses={200: AdminAdministratorListSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    update=extend_schema(
        tags=USER_ADMIN_LIST_TAG,
        summary='Actualizar estado de administrador',
        description='Activa o desactiva el perfil administrador asociado al usuario.',
        parameters=[USER_ID_PARAMETER],
        request=AdminUpdateAdministratorSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class AdminListAdministrador(viewsets.ViewSet):
    """Listado administrativo de otros usuarios administradores."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = AdminAdministratorListSerializer

    def list(self, request):
        """
            Servicio para listar Usuarios administradores. Se necesita autenticación como usuario administrador
        """
        user = User.objects.filter(
            administrator__isnull=False,
        ).exclude(email=self.request.user.email)
        serializer = AdminAdministratorListSerializer(user, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para obtener Usuario administrador. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(administrator__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminAdministratorListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Usuario admiistrador. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateAdministratorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.administrator is not None:
            administrator = get_object_or_404(Administrator, id=instance.administrator.id)
            administrator.is_active = serializer.validated_data['administrator_is_active']
            administrator.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


@extend_schema_view(
    get=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Contar estudiantes y docentes',
        description='Devuelve contadores publicos resumidos de estudiantes registrados y docentes activos.',
        responses={200: USER_COUNT_RESPONSE},
    )
)
class UserCountView(APIView):
    """Expone contadores públicos resumidos de estudiantes y docentes activos."""
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        students = User.objects.filter(student__isnull=False).count()
        teacher = User.objects.filter(
            teacher__isnull=False
        ).exclude(
            teacher__is_active=False
        ).count()

        result = {
            "total_student": students,
            "total_teacher": teacher
        }
        return Response(result, status=HTTP_200_OK)


import urllib.request
from bs4 import BeautifulSoup
import requests


class VerifyOrcid(APIView):
    """Valida superficialmente un ORCID consultando la URL pública."""
    permission_classes = [AllowAny]
    serializer_class = OrcidValidationSerializer

    @extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Validar ORCID',
        description='Recibe un ORCID y valida de forma superficial la disponibilidad de ORCID mediante una consulta HTTP externa.',
        request=OrcidValidationSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: OpenApiResponse(description='Payload invalido.')},
    )

    def post(self, request, format=None):
        serializer = OrcidValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        orcid = serializer.validated_data['orcid']
        url = 'https://orcid.org/0000-0002-9659-7109'
        opener = urllib.request.FancyURLopener({})
        f = opener.open(url)
        content = f.read()

        try:
            return Response({"message": "OK"}, status=HTTP_200_OK)
        except:
            return Response({"message": "invalid"}, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Contar docentes y expertos por estado',
        description='Devuelve conteos publicos de docentes, expertos y estudiantes, separando aprobados y no aprobados.',
        responses={200: USER_TOTAL_ROLE_RESPONSE},
    )
)
class TotalExpertTeacher(APIView):
    """Devuelve el resumen público de usuarios por rol y estado de aprobación."""
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        total_expert_approved = User.objects.filter(
            collaboratingExpert__isnull=False,
        ).exclude(
            collaboratingExpert__is_active=False
        ).count()
        total_expert_disapproved = User.objects.filter(
            collaboratingExpert__isnull=False,
        ).exclude(
            collaboratingExpert__is_active=True
        ).count()
        total_teacher_approved = User.objects.filter(
            teacher__isnull=False,
        ).exclude(
            teacher__is_active=False
        ).count()
        total_teacher_disapproved = User.objects.filter(
            teacher__isnull=False,
        ).exclude(
            teacher__is_active=True
        ).count()
        total_student = User.objects.filter(
            student__isnull=False,
        ).count()

        result = {
            "total_expert_approved": total_expert_approved,
            "total_expert_disapproved": total_expert_disapproved,
            "total_teacher_approved": total_teacher_approved,
            "total_teacher_disapproved": total_teacher_disapproved,
            "total_student": total_student,
        }
        return Response(result, status=HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Iniciar sesion',
        description='Valida credenciales y emite tokens JWT solo si la cuenta y el rol operativo estan activos.',
        request=MyTokenObtainPairSerializer,
        responses={200: USER_TOKEN_RESPONSE, 401: OpenApiResponse(description='Credenciales invalidas o usuario inactivo.')},
    )
)
class MyObtainTokenPairView(TokenObtainPairView):
    """Punto de entrada de login basado en JWT para el frontend.

    Durante la migracion conserva el JSON legacy con `access` y `refresh`,
    pero ademas emite ambas credenciales en cookies HttpOnly para que el
    frontend pueda empezar a probar el nuevo contrato sin romperse.
    """

    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Autentica y adjunta cookies JWT cuando el login es exitoso."""

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200 and isinstance(response.data, dict):
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            if access_token and refresh_token:
                set_auth_cookies(response, access_token, refresh_token)
                set_csrf_cookie(request, response)

        return response


@extend_schema_view(
    post=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Refrescar token JWT',
        description='Recibe un refresh token valido y devuelve un nuevo access token para mantener la sesion activa.',
        request=USER_TOKEN_REFRESH_REQUEST,
        responses={
            200: USER_TOKEN_REFRESH_RESPONSE,
            401: OpenApiResponse(description='Refresh token invalido o expirado.'),
        },
    )
)
class TokenRefreshSwaggerView(TokenRefreshView):
    """Wrapper de SimpleJWT con soporte de refresh por body o por cookie.

    Durante la migracion se mantiene el contrato legacy que acepta `refresh`
    en el body, pero si el cliente no lo envia se intenta leer desde la cookie
    HttpOnly `roa_refresh`.
    """

    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        """Refresca el access token y reemite cookies cuando corresponde."""

        data = request.data.copy()
        refresh_from_body = data.get('refresh')
        refresh_token = refresh_from_body or get_refresh_token_from_request(request)
        if refresh_from_body is None and refresh_token:
            enforce_csrf(request)
        if refresh_token:
            data['refresh'] = refresh_token
            request._full_data = data

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200 and isinstance(response.data, dict):
            access_token = response.data.get('access')
            rotated_refresh = response.data.get('refresh', refresh_token)
            if access_token:
                set_auth_cookies(response, access_token, rotated_refresh)
                set_csrf_cookie(request, response)

        return response


@extend_schema_view(
    post=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Cerrar sesion',
        description=(
            'Invalida el refresh token si existe y limpia las cookies JWT del backend. '
            'Durante la migracion acepta `refresh` por body o por cookie.'
        ),
        request=USER_TOKEN_REFRESH_REQUEST,
        responses={
            200: USER_MESSAGE_RESPONSE,
        },
    )
)
class LogoutAPIView(APIView):
    """Cierra sesion del lado servidor invalidando refresh y limpiando cookies."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """Blacklistea el refresh token cuando es valido y limpia cookies."""

        refresh_from_body = request.data.get('refresh')
        refresh_token = refresh_from_body or get_refresh_token_from_request(request)

        if refresh_from_body is None and refresh_token:
            enforce_csrf(request)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                # Logout se mantiene idempotente: aunque el token ya sea invalido
                # o este expirado, igual se limpian cookies del cliente.
                pass

        response = Response({'message': 'Logout successful'}, status=HTTP_200_OK)
        clear_auth_cookies(response)
        clear_csrf_cookie(response)
        return response


@extend_schema_view(
    get=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Inicializar cookie CSRF',
        description=(
            'Entrega o renueva la cookie CSRF que el frontend debe reenviar como '
            '`X-CSRFToken` cuando use autenticacion por cookies HttpOnly.'
        ),
        responses={200: USER_MESSAGE_RESPONSE},
    )
)
class CsrfCookieAPIView(APIView):
    """Inicializa la cookie CSRF usada por el frontend SPA."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """Entrega una respuesta ligera y asegura que la cookie CSRF exista."""

        response = Response(
            {
                'message': 'CSRF cookie set successfully',
                'cookie': 'csrftoken',
            },
            status=HTTP_200_OK,
        )
        set_csrf_cookie(request, response)
        return response


@extend_schema_view(
    post=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Verificar token JWT',
        description='Valida si un token JWT sigue siendo valido sin devolver datos adicionales.',
        request=USER_TOKEN_VERIFY_REQUEST,
        responses={
            200: OpenApiResponse(description='Token valido.'),
            401: OpenApiResponse(description='Token invalido o expirado.'),
        },
    )
)
class TokenVerifySwaggerView(TokenVerifyView):
    """Wrapper de SimpleJWT para documentar la verificacion de token en Swagger."""

    authentication_classes = ()


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@extend_schema_view(
    get=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Obtener datos del usuario autenticado',
        description='Devuelve datos basicos, roles activos y perfiles relacionados del usuario autenticado.',
        responses={200: UserLoginDataSerializer, 401: OpenApiResponse(description='No autenticado.')},
    )
)
class UserAPIView(RetrieveAPIView):
    """Devuelve los datos de sesion del usuario autenticado.

    Este endpoint funciona como punto de rehidratacion del frontend: acepta
    bearer legacy o cookie `roa_access` y, cuando la sesion es valida, renueva
    tambien la cookie CSRF para los siguientes requests mutables.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = UserLoginDataSerializer

    def retrieve(self, request, *args, **kwargs):
        """Responde con el usuario autenticado y refresca la cookie CSRF."""

        response = super().retrieve(request, *args, **kwargs)
        if response.status_code == 200:
            set_csrf_cookie(request, response)
        return response

    def get_object(self):
        return self.request.user


@extend_schema_view(
    put=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Cambiar contrasena',
        description='Permite cambiar la contrasena del usuario autenticado cuando el `id` de la ruta coincide con su cuenta.',
        parameters=[USER_PK_PARAMETER],
        request=ChangePasswordSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: USER_MESSAGE_RESPONSE},
    ),
    patch=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Cambiar contrasena parcialmente',
        description='Mismo flujo que PUT, conservado para clientes que actualizan parcialmente.',
        parameters=[USER_PK_PARAMETER],
        request=ChangePasswordSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: USER_MESSAGE_RESPONSE},
    ),
)
class ChangePasswordView(UpdateAPIView):
    """Permite al usuario autenticado cambiar su propia contraseña."""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        if (pk == self.request.user.id):
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                instance.set_password(serializer.validated_data['password'])
                instance.save()
                return Response({"message": "User updated successfully", "status": "Ok"}, status=HTTP_200_OK)
            else:
                return Response({"message": "failed", "details": serializer.errors}, status=HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "The user does not have permissions to update."}, status=HTTP_400_BAD_REQUEST)


mail = SendMail()


class RequestPasswordResetEmail(GenericAPIView):
    """Inicia el flujo de reseteo de contraseña por correo.

    Mantiene un comportamiento heredado especial para estudiantes con
    discapacidad, donde el reseteo no usa enlace sino una regeneración directa.
    """

    permission_classes = [AllowAny]
    serializer_class = RequestPasswordResetEmailSerializer

    @extend_schema(
        tags=USER_AUTH_TAG,
        summary='Solicitar reseteo de contrasena',
        description=(
            'Recibe el correo de la cuenta y envia un enlace de recuperacion. '
            'Para estudiantes con discapacidad conserva el flujo heredado de regeneracion directa.'
        ),
        request=RequestPasswordResetEmailSerializer,
        responses={200: USER_PASSWORD_RESET_RESPONSE, 404: OpenApiResponse(description='Correo no registrado.')},
    )

    def post(self, request):
        data = {request: request, 'data': request.data}
        email = request.data['email']
        get_object_or_404(User, email=email)
        user = User.objects.get(email=email)
        if user.student_id is not None:
            student = Student.objects.get(id=user.student_id)
            if student.has_disability is True:
                date_birthday = student.birthday
                email = user.email
                email_name = email.split("@")
                user.set_password(str(email_name[0]) + str(date_birthday))
                user.save()
                return Response({"message": " Reset password successful", "status": 201}, status=HTTP_200_OK)

        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)
        absurl = get_domain_host_roa() + '/#/password-resed/' + uidb64 + '/' + token + '/'
        mail.sendMailTest(user.email, absurl, user.first_name)
        return Response({
            "message": "We have send you a link to reset your password",
            'token': token,
            'uidb64': uidb64
        }, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Verificar token de reseteo',
        description='Valida que el `uidb64` y el token de recuperacion sigan siendo correctos antes de aceptar una nueva contrasena.',
        parameters=[USER_UIDB64_PARAMETER, USER_VERIFY_TOKEN_PARAMETER],
        responses={200: USER_PASSWORD_TOKEN_RESPONSE, 401: USER_PASSWORD_TOKEN_RESPONSE},
    )
)
class PasswordTokenCkeckAPI(GenericAPIView):
    """Verifica si el token de reseteo recibido sigue siendo válido."""

    permission_classes = [AllowAny]
    serializer_class = serializers.Serializer

    def get(self, request, uidb64, token):
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({"error": "Token is no valid, please request a new one"}, status=HTTP_401_UNAUTHORIZED)
            return Response({'success': True, 'message': 'Credential valid', 'uidb64': uidb64, 'token': token},
                            status=HTTP_200_OK)
        except DjangoUnicodeDecodeError as identifier:
            return Response({"error": "Token is no valid, please request a new one."}, status=HTTP_401_UNAUTHORIZED)


@extend_schema_view(
    patch=extend_schema(
        tags=USER_AUTH_TAG,
        summary='Guardar nueva contrasena',
        description='Aplica la nueva contrasena usando el `uidb64` y token validados del flujo de recuperacion.',
        request=SetNewPasswordSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 401: OpenApiResponse(description='Token invalido o expirado.')},
    )
)
class SetNewPasswordAPIView(GenericAPIView):
    """Cierra el flujo de reseteo aplicando la nueva contraseña."""

    permission_classes = [AllowAny, ]
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'status': True, 'message': 'Password reset succes.'}, status=HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Consultar foto de perfil',
        description='Devuelve el recurso de usuario usado para actualizar la imagen de perfil.',
        parameters=[USER_PK_PARAMETER],
        responses={200: UserUpdatePictureSerializer, 404: OpenApiResponse(description='Usuario no encontrado.')},
    ),
    put=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Actualizar foto de perfil',
        description='Actualiza exclusivamente el archivo de imagen del usuario autenticado.',
        parameters=[USER_PK_PARAMETER],
        request=UserUpdatePictureSerializer,
        responses={200: UserUpdatePictureSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    patch=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Actualizar parcialmente foto de perfil',
        description='Permite cambiar solo el campo `image` del usuario.',
        parameters=[USER_PK_PARAMETER],
        request=UserUpdatePictureSerializer,
        responses={200: UserUpdatePictureSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
)
class UpdateUserProfilePicture(RetrieveUpdateAPIView):
    """Actualiza solo la foto de perfil del usuario autenticado."""

    permission_classes = [IsAuthenticated, (IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser)]
    serializer_class = UserUpdatePictureSerializer
    queryset = User.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Consultar preferencias de estudiante por correo',
        description='Devuelve las preferencias asociadas al perfil estudiante de la cuenta identificada por correo.',
        parameters=[USER_EMAIL_PARAMETER],
        responses={200: UserListSerializers, 404: OpenApiResponse(description='Usuario no encontrado.')},
    )
)
class GetStudentPreferences(RetrieveAPIView):
    """Expone las preferencias de un estudiante identificado por correo."""

    lookup_field = 'email'
    permission_classes = [AllowAny]
    serializer_class = UserListSerializers

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        email = self.kwargs['email']
        obj = User.objects.filter(email=email)
        return obj


@extend_schema_view(
    get=extend_schema(
        tags=USER_REPORT_TAG,
        summary='Generar reporte administrativo de docentes',
        description='Lista docentes y sus OAs creados aplicando filtros por carga, texto, ubicacion institucional y rango de fechas.',
        parameters=USER_REPORT_PARAMETERS,
        responses={200: UserReportSerializer(many=True), 401: OpenApiResponse(description='No autenticado.'), 403: OpenApiResponse(description='Requiere rol administrador.')},
    )
)
class ReportListAPIView(ListAPIView):
    """Reporte administrativo de docentes con filtros y objetos creados."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = UserReportSerializer
    pagination_class = UserReportPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
    }

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        upload = self.request.query_params.get("upload")
        query = self.request.query_params.get("query")
        city = self.request.query_params.get("city")
        university = self.request.query_params.get("university")
        campus = self.request.query_params.get("campus")
        created_init = self.request.query_params.get("created_init")
        created_end = self.request.query_params.get("created_end")

        users = User.objects.filter(
            teacher_id__isnull=False
        )

        if upload == "upload":
            users = users.filter(
                metadata_created__isnull=False
            )
        elif upload == "not_upload":
            users = User.objects.filter(
                metadata_created__isnull=True
            )

        if query not in (None, ""):
            users = users.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__exact=query),
            )

        if city is not None and city.isnumeric():
            users = users.filter(
                city_id=int(city)
            )

        if university is not None and university.isnumeric():
            users = users.filter(
                university_id=int(university)
            )

        if campus is not None and campus.isnumeric():
            users = users.filter(
                campus_id=int(campus)
            )
        if created_init is not None and created_end is not None:
            date_init = datetime.strptime(created_init, '%Y-%m-%d').date()
            date_end = datetime.strptime(created_end, '%Y-%m-%d').date()
            users = users.filter(
                created__date__range=[date_init, date_end]
            )

        return users.order_by('-pk').distinct('id')


@extend_schema_view(
    post=extend_schema(
        tags=USER_ACCOUNT_TAG,
        summary='Enviar mensaje de contacto',
        description='Envia el mensaje del formulario publico de contacto al correo institucional definido para atencion.',
        request=EmailContacSerializer,
        responses={200: USER_MESSAGE_RESPONSE, 400: USER_MESSAGE_RESPONSE},
    )
)
class sendEmailContact(CreateAPIView):
    """Envia mensajes del formulario publico de contacto al buzon institucional."""

    permission_classes = [AllowAny]
    serializer_class = EmailContacSerializer

    def create(self, request, *args, **kwargs):
        serializer = EmailContacSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            for recipient_email, recipient_name in get_user_admin_notification_recipients():
                mail_aproved.sendEmailContactAdmin(
                    recipient_email,
                    recipient_name,
                    serializer['name'].value,
                    serializer['email'].value,
                    serializer['content'].value,
                    CONTACT_ROA_INSTANCE_NAME,
                    CONTACT_ROA_PUBLIC_URL,
                )
        except Exception:
            logger.exception("Error enviando correo de contacto al buzon institucional")
            return Response({'code': 400, 'message': 'Failed to send email'}, status=HTTP_400_BAD_REQUEST)
        return Response({'code': 200, 'message': 'Email sent successfully'}, status=HTTP_200_OK)
