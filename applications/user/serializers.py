"""Serializers del modulo `user`.

Este archivo concentra lógica de negocio de entrada y salida para varios flujos del
proyecto: autenticación, registro por rol, actualización de perfiles,
listados administrativos, reportes y recuperación de contraseña.
"""

import re
from urllib.parse import urlparse

from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from applications.user.utils import Util
from rest_framework.response import Response
from roabackend.settings import DOMAIN
from rest_framework import serializers, pagination
from rest_framework.validators import UniqueValidator
from applications.education_level.serializers import EducationLevelListSerializer
from applications.knowledge_area.serializers import KnowledgeAreaListSerializer
from applications.preferences.serializers import PreferencesListSerializer, PreferencesListSerializersTest
from applications.profession.serializers import ProfessionListSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.preferences.models import Preferences
from applications.profession.models import Profession

from .models import (
    User,
    Administrator,
    Student,
    Teacher,
    CollaboratingExpert,
    PublicProfile,
    UserLink,
    AcademicDegree,
)
from ..learning_object_file.serializers import LearningObjectFileSerializer
from ..learning_object_metadata.models import LearningObjectMetadata


"""Helpers de colecciones simples reutilizados en payloads por rol."""
class ArrayIntegerSerializer(serializers.ListField):
    """Lista tipada de enteros para ids relacionados."""

    children = serializers.IntegerField(required=True)


class ArrayStringSerializer(serializers.ListField):
    """Lista tipada de strings para colecciones simples como `roles`."""

    child = serializers.CharField(required=True)


"""Ubicacion de la cuenta principal."""
# Campos de ubicacion de `User`, en el orden en que se exponen en el API.
USER_LOCATION_FIELDS = (
    'country_code',
    'country_name',
    'province_code',
    'province_name',
    'city_name',
    'university_name',
)


class UserLocationSerializer(serializers.Serializer):
    """Ubicacion como texto, tomada del catalogo geografico del frontend.

    Todos los campos son opcionales; las subclases definen en
    `required_fields` cuales exige su flujo. `country_code` se normaliza a
    mayusculas y debe ser un codigo ISO 3166-1 alpha-2.
    """

    required_fields = ()

    country_code = serializers.RegexField(
        r'^[A-Za-z]{2}$', max_length=2, required=False, allow_blank=True, allow_null=True,
        error_messages={'invalid': 'Debe ser un codigo de pais ISO de 2 letras.'},
    )
    country_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    province_code = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    province_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    city_name = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    university_name = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)

    def validate_country_code(self, value):
        return value.upper() if value else value

    def validate(self, attrs):
        missing_fields = {
            field: ["Este campo es requerido para docentes y expertos."]
            for field in self.required_fields
            if attrs.get(field) in (None, "")
        }
        if missing_fields:
            raise serializers.ValidationError(missing_fields)
        return attrs


class UserLocationRequiredSerializer(UserLocationSerializer):
    """Ubicacion exigida en el registro de docentes y expertos.

    La provincia queda opcional porque el catalogo geografico no tiene
    provincias para algunos paises.
    """

    required_fields = ('country_code', 'country_name', 'city_name', 'university_name')


"""Serializers básicos de administración y cuenta principal."""
class AdminSerializer(serializers.ModelSerializer):
    """Representación genérica del perfil administrativo."""

    class Meta:
        model = Administrator
        fields = ('__all__')


class UserSerializer(serializers.ModelSerializer):
    """Serializer plano del modelo `User` para usos internos genéricos."""

    class Meta:
        model = User
        fields = ('__all__')


class UserFullName(serializers.ModelSerializer):
    """Salida reducida con nombres, apellidos y `user_key` del usuario.

    `user_key` es el identificador público con el que el frontend enlaza el
    autor de un OA a su página `/author/<user_key>`.
    """

    class Meta:
        model = User
        fields = ('user_key', 'first_name', 'last_name')


class UserAdminSerializer(serializers.Serializer):
    """Entrada para creación administrativa de usuarios internos."""

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True, validators=[
        UniqueValidator(queryset=User.objects.all(),
                        message="Este correo ya esta registrado.",
                        )])
    password = serializers.CharField(required=True, min_length=8)
    country = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    # image = serializers.ImageField(required=False)
    observation = serializers.CharField(default="")


class UserAdmiUpdatenSerializer(serializers.Serializer):
    """Entrada para actualización del perfil administrativo."""

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    # image = serializers.ImageField(required=False)
    is_active = serializers.BooleanField(default=True)
    observation = serializers.CharField(default="")


"""Serializers de actualización por rol."""
class UserUpdateSerializer(serializers.Serializer):
    """Campos comunes del update de la cuenta principal.

    Los atributos específicos de estudiante, docente y experto se validan con
    serializers separados dentro del flujo de actualización.
    """

    roles = ArrayStringSerializer()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    # La ubicacion se valida aparte con `UserLocationSerializer`.
    # image = serializers.ImageField(required=True)


class UserUpdatePictureSerializer(serializers.ModelSerializer):
    """Actualización acotada de la imagen de perfil."""

    class Meta:
        model = User
        fields = ('image',)


class StudentUpdateSerializer(serializers.Serializer):
    """Entrada de actualización para el perfil estudiante."""

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    birthday = serializers.DateField(required=True)
    has_disability = serializers.BooleanField(default=False)
    disability_description = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    education_levels = ArrayIntegerSerializer()
    knowledge_areas = ArrayIntegerSerializer()
    preferences = ArrayIntegerSerializer()

    def validate_education_levels(self, value):
        for i in value:
            if not EducationLevel.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe el nivel de educación con id {i}")
        return value

    def validate_knowledge_areas(self, value):
        for i in value:
            if not KnowledgeArea.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe el area de conocimiento con id {i}")
        return value

    def validate_preferences(self, value):
        for i in value:
            if not Preferences.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe las preferencias con id {i}")
        return value


class TeacherUpdateSerializer(serializers.Serializer):
    """Entrada de actualización para el perfil docente."""

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    professions = ArrayIntegerSerializer()

    def validate_professions(self, value):
        for i in value:
            if not Profession.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe la profesión con id {i}")
        return value


class CollaboratingExpertUpdateSerializer(serializers.Serializer):
    """Entrada de actualización para el perfil de experto colaborador."""

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    expert_level = serializers.CharField(required=True)
    web = serializers.URLField(default=None)
    academic_profile = serializers.CharField(default=None)


"""Serializers de lectura y registro por rol."""
class UserListSerializer(serializers.ModelSerializer):
    """Salida administrativa de usuario con perfil admin."""

    administrator = AdminSerializer()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'image',
            'image_url',
            'administrator'
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url


class UserCommentSerializer(serializers.ModelSerializer):
    """Salida breve para comentarios u otras vistas públicas ligeras."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'user_key',
            'first_name',
            'last_name',
            'image_url',
            'email'
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url


class RoleSerializer(serializers.Serializer):
    """Entrada base para registro de usuarios por rol.

    Reúne los campos comunes y deja a serializers específicos por rol
    la validación de atributos adicionales.
    """

    roles = ArrayStringSerializer()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    image = serializers.ImageField(default='img/user.png')
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(required=True, min_length=8)
    # La ubicacion de docentes y expertos se valida con
    # `UserLocationRequiredSerializer`.

    role_list = []

    def validate_roles(self, value):
        allowed_roles = {'student', 'teacher', 'expert'}
        roles = [role.strip() if isinstance(role, str) else role for role in value]

        if not roles:
            raise serializers.ValidationError("Debe seleccionar un rol para registrar el usuario.")

        if len(roles) != 1:
            raise serializers.ValidationError("El registro permite seleccionar un solo rol.")

        invalid_roles = [role for role in roles if role not in allowed_roles]
        if invalid_roles:
            raise serializers.ValidationError("Rol no valido. Use student, teacher o expert.")

        self.role_list = roles
        return self.role_list

    def validate_email(self, value):
        if len(self.role_list) == 1 and "student" in self.role_list:
            pass
        # else:
        #     if ".edu" not in value:
        #         raise serializers.ValidationError("El correo debe ser institucionals")
        return value


class StudentCreateSerializer(serializers.Serializer):
    """Entrada de registro para el perfil estudiante."""

    birthday = serializers.DateField(required=True)
    has_disability = serializers.BooleanField(default=False)
    disability_description = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    education_levels = ArrayIntegerSerializer()
    knowledge_areas = ArrayIntegerSerializer()
    preferences = ArrayIntegerSerializer()

    def validate_education_levels(self, value):
        for i in value:
            if not EducationLevel.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe el nivel de educación con id {i}")
        return value

    def validate_knowledge_areas(self, value):
        for i in value:
            if not KnowledgeArea.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe el area de conocimiento con id {i}")
        return value

    def validate_preferences(self, value):
        for i in value:
            if not Preferences.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe las preferencias con id {i}")
        return value


class TeacherCreateSerializer(serializers.Serializer):
    """Entrada de registro para el perfil docente."""

    professions = ArrayIntegerSerializer()

    def validate_professions(self, value):
        for i in value:
            if not Profession.objects.filter(pk=i).exists():
                raise serializers.ValidationError(f"No existe la profesión con id {i}")
        return value


class CollaboratingExpertCreateSerializer(serializers.Serializer):
    """Entrada de registro para el perfil de experto colaborador."""

    expert_level = serializers.CharField(required=True)
    web = serializers.CharField(default=None)
    academic_profile = serializers.CharField(default=None)


"""Serializers de lectura expandida usados por el frontend y listados admin."""
class StudentListSerializer(serializers.ModelSerializer):
    """Salida expandida del perfil estudiante con relaciones anidadas."""

    education_levels = EducationLevelListSerializer(many=True)
    knowledge_areas = KnowledgeAreaListSerializer(many=True)
    preferences = PreferencesListSerializer(many=True)

    class Meta:
        model = Student
        fields = (
            'id',
            'birthday',
            'has_disability',
            'disability_description',
            'is_active',
            'education_levels',
            'knowledge_areas',
            'preferences'
        )

class UserListSerializersPreferences(serializers.ModelSerializer):
    """Salida reducida usada cuando solo interesa exponer preferencias."""

    preferences = PreferencesListSerializersTest(many=True)

    class Meta:
        model = Student
        fields = (
            'preferences',
        )


class TeacherListSerializer(serializers.ModelSerializer):
    """Salida expandida del perfil docente."""

    professions = ProfessionListSerializer(many=True)

    class Meta:
        model = Teacher
        fields = (
            'id',
            'professions',
            'is_active'
        )


class ExpertListSerializer(serializers.ModelSerializer):
    """Salida expandida del perfil de experto colaborador."""

    class Meta:
        model = CollaboratingExpert
        fields = (
            'id',
            'expert_level',
            'web',
            'academic_profile',
            'is_active'
        )


class AdministratorListSerializer(serializers.ModelSerializer):
    """Salida completa del perfil administrativo."""

    class Meta:
        model = Administrator
        fields = (
            '__all__'
        )


class GeneralUserListSerializer(serializers.ModelSerializer):
    """Salida completa de usuario para vistas generales del frontend.

    Expone perfiles relacionados ya serializados y deriva la lista de roles
    visibles a partir del estado activo de cada perfil.
    """

    student = StudentListSerializer()
    teacher = TeacherListSerializer()
    collaboratingExpert = ExpertListSerializer()
    roles = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'roles',
            'first_name',
            'last_name',
            'email',
            'image',
            'student',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
            'user_key',
        ) + USER_LOCATION_FIELDS

    @extend_schema_field(OpenApiTypes.URI)
    def get_image(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_roles(self, obj):
        role_lis = []
        if obj.student is not None:
            role_lis.append('student')
        if obj.teacher is not None and obj.teacher.is_active:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active:
            role_lis.append('expert')
        return role_lis


class GeneralUserStudent_View_ListSerializer(serializers.ModelSerializer):
    """Salida reducida de usuario para vistas estudiantiles."""

    roles = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'roles',
            'first_name',
            'last_name',
            'email',
            'image',

            'created',
            'modified',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_roles(self, obj):
        role_lis = []
        if obj.student is not None:
            role_lis.append('student')
        if obj.teacher is not None and obj.teacher.is_active:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active:
            role_lis.append('expert')
        return role_lis


class UserLoginDataSerializer(serializers.ModelSerializer):
    """Salida usada durante login para resolver roles activos del usuario."""

    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'roles',
            'first_name',
            'last_name',
            'email',
            'image',
            'student',
            'teacher',
            'collaboratingExpert',
            'administrator',
        )

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_roles(self, obj):
        role_lis = []
        if obj.student is not None:
            role_lis.append('student')
        if obj.teacher is not None and obj.teacher.is_active:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active:
            role_lis.append('expert')
        if obj.administrator is not None and obj.administrator.is_active:
            role_lis.append('administrator')
        if obj.is_superuser:
            role_lis.append('superuser')
        return role_lis


"""Serializers administrativos para aprobación, rechazo y listados por rol."""
class AdminDisaprovedTeacherCollaboratingExpertSerializer(serializers.ModelSerializer):
    """Lista usuarios con perfiles docente/experto pendientes o desaprobados."""

    teacher = TeacherListSerializer()
    collaboratingExpert = ExpertListSerializer()
    rol_solicitados = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'rol_solicitados',
            'first_name',
            'last_name',
            'email',
            'image',
            'image_url',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_rol_solicitados(self, obj):
        role_lis = []
        if obj.teacher is not None and obj.teacher.is_active is False:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active is False:
            role_lis.append('expert')
        return role_lis


class AdminAprovedTeacherCollaboratingExpertSerializer(serializers.ModelSerializer):
    """Lista usuarios con perfiles docente/experto aprobados."""

    teacher = TeacherListSerializer()
    collaboratingExpert = ExpertListSerializer()
    rol_aprovados = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'rol_aprovados',
            'first_name',
            'last_name',
            'email',
            'image_url',
            'image',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_rol_aprovados(self, obj):
        role_lis = []
        if obj.teacher is not None and obj.teacher.is_active is True:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active is True:
            role_lis.append('expert')
        return role_lis


class AdminAprovedTeacherCollaboratingExpertSerializer(serializers.ModelSerializer):
    """Duplicado heredado del serializer de aprobados."""

    teacher = TeacherListSerializer()
    collaboratingExpert = ExpertListSerializer()
    rol_aprovados = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'rol_aprovados',
            'first_name',
            'last_name',
            'email',
            'image_url',
            'image',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_rol_aprovados(self, obj):
        role_lis = []
        if obj.teacher is not None and obj.teacher.is_active is True:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active is True:
            role_lis.append('expert')
        return role_lis


class AdminAprovedTeacherCollaboratingExpertWithOaSerializer(serializers.ModelSerializer):
    """Lista perfiles aprobados junto con los objetos de aprendizaje creados."""

    teacher = TeacherListSerializer()
    collaboratingExpert = ExpertListSerializer()
    rol_aprovados = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    learning_objects = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_learning_objects(self, obj):
        objects = LearningObjectMetadata.objects.filter(user_created=obj)
        serializer = LearningObjectMetadataReport(objects, many=True)
        return serializer.data

    class Meta:
        model = User
        fields = (
            'id',
            'rol_aprovados',
            'first_name',
            'last_name',
            'email',
            'image_url',
            'image',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
            'learning_objects',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_rol_aprovados(self, obj):
        role_lis = []
        if obj.teacher is not None and obj.teacher.is_active is True:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active is True:
            role_lis.append('expert')
        return role_lis


class AdminStudentListSerializer(serializers.ModelSerializer):
    """Salida administrativa de usuarios con perfil estudiante."""

    student = StudentListSerializer()
    # collaboratingExpert=ExpertListSerializer()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'image',
            'image_url',
            'student',
            'created',
            'modified',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url


class AdminTeacherListSerializer(serializers.ModelSerializer):
    """Salida administrativa de usuarios con perfil docente."""

    teacher = TeacherListSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'image',
            'teacher',
            'created',
            'modified',
        )


class AdminCollaboratingExpertListSerializer(serializers.ModelSerializer):
    """Salida administrativa de usuarios con perfil experto colaborador."""

    collaboratingExpert = ExpertListSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'image',
            'collaboratingExpert',
            'created',
            'modified',
        )


class AdminAdministratorListSerializer(serializers.ModelSerializer):
    """Salida administrativa de usuarios con perfil administrador."""

    administrator = AdministratorListSerializer()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'image',
            'image_url',
            'administrator',
            'created',
            'modified',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN + obj.image.url


class UpdateTecherCollaboratingExpertDisapprovedSerializer(serializers.Serializer):
    """Payload administrativo para desaprobar perfiles docentes y/o experto."""

    teacher_is_active = serializers.BooleanField(default=False)
    expert_is_active = serializers.BooleanField(default=False)


class UpdateTecherCollaboratingExpertApproveedSerializer(serializers.Serializer):
    """Payload administrativo para aprobar perfiles docentes y/o experto."""

    teacher_is_active = serializers.BooleanField(default=True)
    expert_is_active = serializers.BooleanField(default=True)


class AdminUpdateStudentSerializer(serializers.Serializer):
    """Payload administrativo para activar o desactivar estudiantes."""

    student_is_active = serializers.BooleanField(default=False)


class AdminUpdateCollaboratingExpertSerializer(serializers.Serializer):
    """Payload administrativo para activar o desactivar expertos."""

    expert_is_active = serializers.BooleanField(default=False)


class AdminUpdateAdministratorSerializer(serializers.Serializer):
    """Payload administrativo para activar o desactivar administradores."""

    administrator_is_active = serializers.BooleanField(default=False)


"""Serializers de autenticación, recuperación de cuenta y reportes."""
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Emite JWT solo para cuentas y perfiles marcados como activos.

    El proyecto distingue entre activación de cuenta (`is_account_active`) y
    aprobación operativa del rol (`is_active`). Este serializer conserva ambas
    verificaciones antes de emitir el token.

    Todos los errores de login responden `detail` y `code`. El frontend
    traduce el mensaje a partir de `code`; `detail` conserva los textos legacy
    en inglés para no romper clientes que todavía comparan ese texto.

    - 401 `no_active_account`: credenciales invalidas.
    - 403 `account_not_verified`: correo sin verificar.
    - 403 `account_pending_approval`: pendiente de aprobación o desactivada.
    """

    ACCOUNT_NOT_VERIFIED_CODE = 'account_not_verified'
    ACCOUNT_NOT_VERIFIED_MESSAGE = 'Account inactive user'
    ACCOUNT_PENDING_APPROVAL_CODE = 'account_pending_approval'
    ACCOUNT_PENDING_APPROVAL_MESSAGE = 'Inactive user'

    @classmethod
    def _account_denied(cls, message, code):
        """Construye el 403 de login con `detail` y `code` en el cuerpo."""

        return PermissionDenied({'detail': message, 'code': code})

    def validate(self, attrs):
        """Expone el `code` de SimpleJWT en el cuerpo del 401.

        DRF solo serializa `detail`; sin esto el frontend no recibe
        `no_active_account` y tendria que depender del status o del texto.
        """

        try:
            return super().validate(attrs)
        except AuthenticationFailed as exc:
            raise AuthenticationFailed({'detail': exc.detail, 'code': exc.get_codes()})

    @classmethod
    def get_token(cls, user):
        # token = super(MyTokenObtainPairSerializer, cls).get_token(user)
        # token['email'] = user.email
        if (user.student is not None and user.student.is_account_active) or (
                user.teacher is not None and user.teacher.is_account_active) or (
                user.collaboratingExpert is not None and user.collaboratingExpert.is_account_active) or user.is_superuser or (
                user.administrator is not None and user.administrator.is_active):
            if ((user.student is not None and user.student.is_active) or (
                    user.teacher is not None and user.teacher.is_active) or (user.collaboratingExpert is not None
                                                                             and user.collaboratingExpert.is_active)) or user.is_superuser or (
                    user.administrator is not None and user.administrator.is_active):
                token = super().get_token(user)
                return token
            else:
                raise cls._account_denied(cls.ACCOUNT_PENDING_APPROVAL_MESSAGE, cls.ACCOUNT_PENDING_APPROVAL_CODE)
        else:
            raise cls._account_denied(cls.ACCOUNT_NOT_VERIFIED_MESSAGE, cls.ACCOUNT_NOT_VERIFIED_CODE)


class ChangePasswordSerializer(serializers.ModelSerializer):
    """Entrada para cambio autenticado de contraseña actual."""

    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        if attrs['password'] == attrs['old_password']:
            raise serializers.ValidationError({"password": "New password cannot be the same as above."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value

    # def update(self, instance, validated_data):
    #     print(instance)
    #     print('********')
    #     pk = self.kwargs['pk']
    #     print(pk)

    #     instance.set_password(validated_data['password'])
    #     instance.save()

    #     return Response({"message": "User updated successfully"})


from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


# from django.contrib.sites.shortcuts import get_current_site
# from django.urls import reverse

class RequestPasswordResetEmailSerializer(serializers.Serializer):
    """Entrada del inicio del flujo de reseteo de contraseña por correo."""

    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ['email']


class SetNewPasswordSerializer(serializers.Serializer):
    """Entrada del cierre del flujo de reseteo de contraseña por correo usando token y uid codificado."""

    password = serializers.CharField(min_length=4, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)


class UserListSerializers(serializers.ModelSerializer):
    """Salida mínima de usuario enfocada en preferencias del estudiante."""

    student = UserListSerializersPreferences()

    class Meta:
        model = User
        fields = (
            'student',
        )


class LearningObjectMetadataReport(serializers.ModelSerializer):
    """Representa objetos creados por un usuario dentro de reportes."""

    learning_object_file = LearningObjectFileSerializer()

    class Meta:
        model = LearningObjectMetadata
        fields = ('author', 'general_title', 'created', 'learning_object_file')


class UserReportSerializer(serializers.ModelSerializer):
    """Salida administrativa para reportes de usuarios y sus objetos creados."""

    # metadata_created = LearningObjectMetadataReport(many=True)
    learning_objects = serializers.SerializerMethodField()

    @extend_schema_field(LearningObjectMetadataReport(many=True))
    def get_learning_objects(self, obj):
        date_init = self.context['request'].query_params.get("created_init")
        date_end = self.context['request'].query_params.get("created_end")
        objects = LearningObjectMetadata.objects.filter(user_created=obj).order_by('-pk')

        if date_init is not None and date_end is not None:
            objects = objects.filter(created__date__range=[date_init, date_end])

        serializer = LearningObjectMetadataReport(objects, many=True)
        return serializer.data

    class Meta:
        model = User
        fields = (
            ('first_name', 'last_name', 'email')
            + USER_LOCATION_FIELDS
            + ('created', 'learning_objects')
        )


class EmailContacSerializer(serializers.Serializer):
    """Entrada del formulario de contacto público."""

    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)
    content = serializers.CharField(required=True)

    class Meta:
        fields = ('email', 'name', 'content')


"""Serializers del perfil público del autor (edición del perfil propio)."""


def _clean_text(value):
    """Guarda texto plano: quita etiquetas HTML y espacios sobrantes."""

    return strip_tags(value).strip()


def _host_matches(host, domain):
    """Indica si `host` es `domain` o un subdominio suyo (www., ec., ...)."""

    return host == domain or host.endswith('.' + domain)


def is_valid_orcid_checksum(orcid):
    """Comprueba el dígito de control de un ORCID `0000-0000-0000-000X`.

    Algoritmo ISO 7064 Mod 11-2 que publica ORCID: detecta un dígito mal
    escrito o dos dígitos intercambiados sin consultar a orcid.org.
    """

    digits = orcid.replace('-', '')
    total = 0
    for digit in digits[:-1]:
        total = (total + int(digit)) * 2
    result = (12 - total % 11) % 11
    expected = 'X' if result == 10 else str(result)
    return digits[-1].upper() == expected


class UserLinkSerializer(serializers.ModelSerializer):
    """Enlace del perfil público con validación de dominio según su tipo."""

    # Dominio esperado por tipo. `scholar` se valida aparte porque cambia el
    # dominio de primer nivel según el país (scholar.google.com, .es, ...).
    # `institutional` y `website` aceptan cualquier dominio.
    LINK_DOMAINS = {
        'orcid': 'orcid.org',
        'scopus': 'scopus.com',
        'researchgate': 'researchgate.net',
        'linkedin': 'linkedin.com',
    }
    SCHOLAR_HOST_REGEX = re.compile(r'^scholar\.google\.[a-z.]+$')
    # El último carácter es el dígito de control y puede ser X; se acepta en
    # minúscula y se guarda en mayúscula.
    ORCID_PATH_REGEX = re.compile(r'^/(\d{4}-\d{4}-\d{4}-\d{3}[\dX])/?$', re.IGNORECASE)
    ORCID_FORMAT_MESSAGE = (
        'El enlace de ORCID debe tener el formato https://orcid.org/0000-0000-0000-0000; '
        'el último carácter puede ser X.'
    )
    ORCID_CHECKSUM_MESSAGE = 'El número de ORCID no es válido. Revisa que esté bien copiado.'

    class Meta:
        model = UserLink
        fields = ('type', 'url', 'order', 'is_visible')

    def validate(self, attrs):
        link_type = attrs['type']
        parsed_url = urlparse(attrs['url'])
        host = (parsed_url.hostname or '').lower()
        label = dict(UserLink.TYPES)[link_type]

        if parsed_url.scheme != 'https':
            raise serializers.ValidationError({'url': ['El enlace debe empezar con https://.']})

        if link_type == 'scholar':
            if not self.SCHOLAR_HOST_REGEX.match(host):
                raise serializers.ValidationError({'url': [f'El enlace de {label} debe ser de scholar.google.']})
        elif link_type in self.LINK_DOMAINS:
            domain = self.LINK_DOMAINS[link_type]
            if not _host_matches(host, domain):
                raise serializers.ValidationError({'url': [f'El enlace de {label} debe ser de {domain}.']})

        if link_type == 'orcid':
            match = self.ORCID_PATH_REGEX.match(parsed_url.path)
            if not match:
                raise serializers.ValidationError({'url': [self.ORCID_FORMAT_MESSAGE]})
            orcid = match.group(1).upper()
            if not is_valid_orcid_checksum(orcid):
                raise serializers.ValidationError({'url': [self.ORCID_CHECKSUM_MESSAGE]})
            attrs['url'] = parsed_url._replace(path=f'/{orcid}').geturl()
        return attrs


class AcademicDegreeSerializer(serializers.ModelSerializer):
    """Título académico del perfil público."""

    MIN_YEAR = 1950

    class Meta:
        model = AcademicDegree
        fields = ('level', 'title', 'institution', 'year', 'is_visible')

    def validate_title(self, value):
        return _clean_text(value)

    def validate_institution(self, value):
        return _clean_text(value)

    def validate_year(self, value):
        current_year = timezone.localdate().year
        if value is not None and not (self.MIN_YEAR <= value <= current_year):
            raise serializers.ValidationError(f'El año debe estar entre {self.MIN_YEAR} y {current_year}.')
        return value


class ReplaceableItemsField(serializers.ListField):
    """Lista de items que se valida completa con `item_serializer_class`.

    Se usa en lugar de un serializer anidado (`many=True`) por dos motivos:
    - los errores salen como lista alineada con los items
      (`[{}, {"url": [...]}]`), que es lo que espera el frontend;
    - en un `PATCH` DRF deja pasar items anidados sin campos requeridos;
      aquí cada item se valida siempre completo.
    """

    item_serializer_class = None

    def to_internal_value(self, data):
        items = super().to_internal_value(data)
        serializer = self.item_serializer_class(data=items, many=True)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        return serializer.validated_data

    def to_representation(self, value):
        # Un perfil sin guardar todavía no puede consultar sus relaciones.
        if value.instance.pk is None:
            return []
        return self.item_serializer_class(value.all(), many=True).data


@extend_schema_field(UserLinkSerializer(many=True))
class UserLinkListField(ReplaceableItemsField):
    item_serializer_class = UserLinkSerializer


@extend_schema_field(AcademicDegreeSerializer(many=True))
class AcademicDegreeListField(ReplaceableItemsField):
    item_serializer_class = AcademicDegreeSerializer


class OwnPublicProfileSerializer(serializers.ModelSerializer):
    """Lectura y guardado del perfil público propio.

    Devuelve todo, también lo marcado como "Solo yo", con la visibilidad ya
    combinada con los valores por defecto. En el guardado:
    - `field_visibility` se mezcla con lo guardado;
    - `links` y `degrees` reemplazan la lista completa si vienen; si la clave
      no viene, esa lista no se toca;
    - todo ocurre en una transacción: si algo falla no se guarda nada.
    """

    MAX_DEGREES = 10

    user_key = serializers.UUIDField(source='user.user_key', read_only=True)
    highest_degree = serializers.SerializerMethodField()
    research_lines = serializers.ListField(
        child=serializers.CharField(max_length=60),
        max_length=5,
        required=False,
    )
    subjects = serializers.ListField(
        child=serializers.CharField(max_length=100),
        max_length=10,
        required=False,
    )
    field_visibility = serializers.DictField(
        child=serializers.ChoiceField(choices=PublicProfile.VISIBILITY_CHOICES),
        required=False,
    )
    links = UserLinkListField(required=False, max_length=len(UserLink.TYPES))
    degrees = AcademicDegreeListField(required=False, max_length=MAX_DEGREES)

    class Meta:
        model = PublicProfile
        fields = (
            'user_key',
            'is_public',
            'headline',
            'faculty',
            'bio',
            'research_lines',
            'subjects',
            'research_group',
            'field_visibility',
            'highest_degree',
            'links',
            'degrees',
        )

    @extend_schema_field(serializers.ChoiceField(choices=AcademicDegree.LEVELS, allow_null=True))
    def get_highest_degree(self, obj):
        # En el perfil propio cuentan también los títulos ocultos.
        return obj.get_highest_degree(only_visible=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['field_visibility'] = instance.get_field_visibility()
        return data

    def validate_headline(self, value):
        return _clean_text(value)

    def validate_faculty(self, value):
        return _clean_text(value)

    def validate_bio(self, value):
        return _clean_text(value)

    def validate_research_group(self, value):
        return _clean_text(value)

    def validate_research_lines(self, value):
        return [_clean_text(item) for item in value]

    def validate_subjects(self, value):
        return [_clean_text(item) for item in value]

    def validate_field_visibility(self, value):
        unknown_fields = sorted(set(value) - set(PublicProfile.VISIBILITY_DEFAULTS))
        if unknown_fields:
            raise serializers.ValidationError(
                f'Campos sin visibilidad configurable: {", ".join(unknown_fields)}.'
            )
        return value

    def validate_links(self, value):
        link_types = [link['type'] for link in value]
        if len(link_types) != len(set(link_types)):
            raise serializers.ValidationError('Hay más de un enlace del mismo tipo.')
        return value

    def update(self, instance, validated_data):
        links = validated_data.pop('links', None)
        degrees = validated_data.pop('degrees', None)
        field_visibility = validated_data.pop('field_visibility', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if field_visibility is not None:
            merged = {**(instance.field_visibility or {}), **field_visibility}
            instance.field_visibility = {
                key: value for key, value in merged.items() if key in PublicProfile.VISIBILITY_DEFAULTS
            }

        with transaction.atomic():
            # Si el usuario aún no tenía fila, este `save` la crea.
            instance.save()
            if links is not None:
                instance.links.all().delete()
                UserLink.objects.bulk_create([UserLink(profile=instance, **link) for link in links])
            if degrees is not None:
                instance.degrees.all().delete()
                AcademicDegree.objects.bulk_create(
                    [AcademicDegree(profile=instance, **degree) for degree in degrees]
                )

        # Las listas cambiaron: descarta lo precargado para responder lo nuevo.
        instance._prefetched_objects_cache = {}
        return instance


class NamedCatalogItemSerializer(serializers.Serializer):
    """Salida mínima `{id, name}` para catálogos de ubicación."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class PublicKnowledgeAreaSerializer(serializers.Serializer):
    """Área de conocimiento con ambos idiomas para el frontend con i18n."""

    id = serializers.IntegerField(read_only=True)
    name_es = serializers.CharField(read_only=True)
    name_en = serializers.CharField(read_only=True)


class PublicAuthorSerializer(serializers.ModelSerializer):
    """Perfil público de un docente, tal como lo ve cualquier visitante.

    Los datos fijos salen de la cuenta y siempre vienen. Los opcionales de
    `PublicProfile` solo vienen si están en "Público" y no están vacíos; si no,
    la clave no aparece en la respuesta. Links y títulos solo los visibles.
    """

    OPTIONAL_FIELDS = ('headline', 'faculty', 'bio', 'research_lines', 'subjects', 'research_group')

    image_url = serializers.SerializerMethodField()
    university = NamedCatalogItemSerializer(read_only=True)
    campus = NamedCatalogItemSerializer(read_only=True)
    professions = ProfessionListSerializer(source='teacher.professions', many=True, read_only=True)
    knowledge_areas = serializers.SerializerMethodField()
    member_since = serializers.IntegerField(source='created.year', read_only=True)

    class Meta:
        model = User
        fields = (
            'user_key',
            'first_name',
            'last_name',
            'email',
            'image_url',
            'university',
            'campus',
            'professions',
            'knowledge_areas',
            'member_since',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        if obj.image:
            return DOMAIN + obj.image.url
        return None

    @extend_schema_field(PublicKnowledgeAreaSerializer(many=True))
    def get_knowledge_areas(self, obj):
        """Áreas distintas de los OA públicos del autor."""

        knowledge_areas = KnowledgeArea.objects.filter(
            knowledge_learningobject__user_created=obj,
            knowledge_learningobject__public=True,
        ).distinct().order_by('name_es')
        return PublicKnowledgeAreaSerializer(knowledge_areas, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            profile = instance.public_profile
        except PublicProfile.DoesNotExist:
            profile = None

        data['links'] = []
        data['degrees'] = []
        if profile is None:
            return data

        for field_name in self.OPTIONAL_FIELDS:
            value = getattr(profile, field_name)
            if value and profile.is_field_public(field_name):
                data[field_name] = value

        highest_degree = profile.get_highest_degree()
        if highest_degree:
            data['highest_degree'] = highest_degree
        data['links'] = [
            {'type': link.type, 'url': link.url}
            for link in profile.links.all()
            if link.is_visible
        ]
        data['degrees'] = [
            {
                'level': degree.level,
                'title': degree.title,
                'institution': degree.institution,
                'year': degree.year,
            }
            for degree in profile.degrees.all()
            if degree.is_visible
        ]
        return data


class AdminTeacherLearningObjectSerializer(serializers.ModelSerializer):
    """OA de un docente en el detalle del admin, con sus totales.

    `views` y `downloads` vienen anotados por la vista; el serializer no
    consulta los contadores por su cuenta.
    """

    avatar = serializers.SerializerMethodField()
    views = serializers.IntegerField(read_only=True)
    downloads = serializers.IntegerField(read_only=True)

    class Meta:
        model = LearningObjectMetadata
        fields = ('id', 'slug', 'general_title', 'avatar', 'created', 'public', 'views', 'downloads')

    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar(self, obj):
        # Sin `request` en el contexto, la URL absoluta se arma con DOMAIN.
        if obj.avatar:
            return DOMAIN + obj.avatar.url
        return None


class AdminTeacherDetailSerializer(AdminDisaprovedTeacherCollaboratingExpertSerializer):
    """Detalle administrativo de un docente, con su perfil público completo.

    `public_profile` usa el mismo formato del perfil propio: trae también lo
    marcado como "Solo yo" y el flag `is_public`, para que el admin vea todo.
    Es `null` si el docente nunca guardó su perfil.

    `learning_objects` trae todos los OA del docente (públicos y no públicos)
    y requiere el `Prefetch` con `to_attr='admin_learning_objects'` que hace
    `AdminDisaprovedTeacher.retrieve`.
    """

    public_profile = serializers.SerializerMethodField()
    university = NamedCatalogItemSerializer(read_only=True, allow_null=True)
    campus = NamedCatalogItemSerializer(read_only=True, allow_null=True)
    learning_objects = AdminTeacherLearningObjectSerializer(
        source='admin_learning_objects',
        many=True,
        read_only=True,
    )

    class Meta(AdminDisaprovedTeacherCollaboratingExpertSerializer.Meta):
        fields = AdminDisaprovedTeacherCollaboratingExpertSerializer.Meta.fields + (
            'public_profile',
            'university',
            'campus',
            'learning_objects',
        )

    @extend_schema_field(OwnPublicProfileSerializer(allow_null=True))
    def get_public_profile(self, obj):
        try:
            profile = obj.public_profile
        except PublicProfile.DoesNotExist:
            return None
        return OwnPublicProfileSerializer(profile).data
