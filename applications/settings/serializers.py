"""Serializers de configuración operativa expuesta por API.

El módulo cubre tres grupos de contratos:
- configuración SMTP persistida
- catálogos de dominios permitidos o restringidos por rol
- validaciones puntuales para filtros, updates de opción y pruebas de conexión
"""

from rest_framework import serializers
from applications.settings import models


USER_TYPE_CHOICES = (
    ("TEACHER", "TEACHER"),
    ("EXPERT", "EXPERT"),
    ("STUDENT", "STUDENT"),
)


class EmailSerializer(serializers.ModelSerializer):
    """Expone la configuración SMTP almacenada en base de datos.

    El password no se devuelve cifrado: la salida publica el resultado de
    `decrypt_password` para que administración pueda inspeccionar o reutilizar
    la configuración actual desde la API.
    """

    class Meta:
        model = models.Email
        fields = ("__all__")

    password = serializers.CharField(
        source='decrypt_password',
        read_only=True,
        help_text="Password SMTP descifrado para lectura administrativa.",
    )


class OptionRegisterEmailExtensionSerializer(serializers.ModelSerializer):
    """Serializer básico del modo de registro por extensión de correo."""

    class Meta:
        model = models.OptionRegisterEmailExtension
        fields = ("type_option","id")


class EmailDomainTeacherSerializer(serializers.ModelSerializer):
    """Lectura expandida de dominios configurados para docentes."""

    option_register_email = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.EmailExtensionsTeacher
        fields = ("id","domain","is_active","option_register_email")


class EmailDomainTeacherCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para dominios de correo de docentes."""

    class Meta:
        model = models.EmailExtensionsTeacher
        fields = "__all__"


class EmailDomainExpertSerializer(serializers.ModelSerializer):
    """Lectura expandida de dominios configurados para expertos."""

    option_register_email = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.EmailExtensionsExpert
        fields = ("id","domain", "is_active", "option_register_email")


class EmailDomainExpertCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para dominios de correo de expertos."""

    class Meta:
        model = models.EmailExtensionsExpert
        fields = "__all__"


class EmailDomainStudentSerializer(serializers.ModelSerializer):
    """Lectura expandida de dominios configurados para estudiantes."""

    option_register_email = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.EmailExtensionsStudent
        fields = ("id", "domain", "is_active", "option_register_email")


class EmailDomainStudentCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para dominios de correo de estudiantes."""

    class Meta:
        model = models.EmailExtensionsStudent
        fields = "__all__"


class UserTypeWithOptionSerializer(serializers.ModelSerializer):
    """Serializer de escritura para relacionar un tipo de usuario con su regla."""

    class Meta:
        model = models.UserTypeWithOption
        fields = "__all__"


class UserTypeWithOptionSerializerList(serializers.ModelSerializer):
    """Lectura con la opción de registro ya expandida para administración."""

    option_register = OptionRegisterEmailExtensionSerializer()

    class Meta:
        model = models.UserTypeWithOption
        fields = ("id", "description", "option_register")


class EmailDomainTypeSerializer(serializers.Serializer):
    """Valida el tipo de usuario que selecciona la tabla de dominios."""

    type = serializers.ChoiceField(
        choices=USER_TYPE_CHOICES,
        help_text="Tipo de usuario que define que tabla de dominios se consulta o modifica.",
    )


class EmailDomainListQuerySerializer(EmailDomainTypeSerializer):
    """Valida los filtros simples usados al listar dominios por tipo."""

    option = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Identificador de la politica de registro usada para filtrar dominios.",
    )


class UserTypeOptionUpdateInputSerializer(serializers.Serializer):
    """Valida la opción de registro antes de actualizar la relación."""

    option_register = serializers.PrimaryKeyRelatedField(
        queryset=models.OptionRegisterEmailExtension.objects.all(),
        help_text="Politica de registro por dominio que se asignara al tipo de usuario.",
    )


class EmailTestingConnectionSerializer(serializers.Serializer):
    """Valida el payload de la prueba de conexión SMTP del administrador."""

    host = serializers.CharField(help_text="Servidor SMTP que se desea probar.")
    username = serializers.CharField(help_text="Usuario SMTP usado en la prueba de conexion.")
    password = serializers.CharField(help_text="Password SMTP temporal usado solo para la prueba.")
    emailtest = serializers.EmailField(help_text="Correo destinatario que recibira el email de prueba.")
    port = serializers.CharField(help_text="Puerto SMTP usado en la prueba.")
    tls = serializers.BooleanField(help_text="Indica si la prueba debe usar TLS.")
    email_from = serializers.EmailField(help_text="Correo remitente usado para enviar la prueba.")

