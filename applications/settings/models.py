"""Modelos de configuración operativa del sistema.

Este módulo agrupa ajustes persistidos en base de datos que afectan el
comportamiento global de la plataforma, en especial:
- credenciales SMTP usadas por los gestores de correo
- reglas de dominios de email permitidos o restringidos por rol

No es configuración estática de Django `settings.py`; son catálogos y valores
operativos que administración puede consultar o modificar desde la app.
"""

import base64
from cryptography.fernet import Fernet
from django.db import models
from model_utils.models import TimeStampedModel
import os
from unipath import Path
import environ
env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


class Email(TimeStampedModel):
    """Configuración SMTP persistida para el envió de correos del sistema.

    El password se almacena cifrado en base de datos y se descifra en tiempo de
    uso con `HASH_KEY` tomada del entorno. Este modelo es la fuente real de
    configuración para varios gestores de correo del proyecto.
    """

    host = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        help_text="Servidor SMTP usado para enviar correos del sistema.",
    )
    username = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Usuario o cuenta SMTP usada para autenticarse con el servidor de correo.",
    )
    password = models.CharField(
        max_length=256,
        null=True,
        help_text="Password SMTP cifrado con HASH_KEY antes de almacenarse.",
    )
    port = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Puerto SMTP usado por la conexion de envio.",
    )
    tls = models.BooleanField(
        default=True,
        help_text="Indica si la conexion SMTP debe usar TLS.",
    )
    email_from = models.EmailField(
        null=True,
        blank=True,
        help_text="Direccion remitente que aparece en los correos enviados por la plataforma.",
    )

    def __str__(self):
        """Devuelve el remitente configurado para administración o debug."""

        return str(self.email_from)

    def decrypt_password(self):
        """Descifra el password almacenado usando la clave del entorno."""

        # pas = base64.urlsafe_b64decode(self.password)
        pas = self.password.encode('utf-8')
        cipher_pass = Fernet(env('HASH_KEY'))
        decode_pass = cipher_pass.decrypt(pas)
        decode_pass = decode_pass.decode("utf-8")
        return decode_pass

    def encrypt_password(self, password):
        """Cifra un password plano antes de persistirlo en la base de datos."""

        pas = str(password).encode()
        cipher_pass = Fernet(env('HASH_KEY'))
        encrypt_pass = cipher_pass.encrypt(pas)
        return encrypt_pass


class OptionRegisterEmailExtension(TimeStampedModel):
    """Define la política general aplicada a dominios de registro por email.

    `ALL`, `EXCEPT` y `ONLY` actúan como modo operativo para interpretar las
    listas de dominios asociadas luego a estudiantes, docentes o expertos.
    """

    TYPE_CHOICES_OPTION = (
        ('ALL', 'ALL'),
        ('EXCEPT', 'EXCEPT'),
        ('ONLY', 'ONLY'),
    )
    type_option = models.CharField(
        max_length=40,
        choices=TYPE_CHOICES_OPTION,
        blank=True,
        null=True,
        help_text="Modo de validacion de dominios de correo: ALL permite todos, ONLY permite solo listados y EXCEPT excluye listados.",
    )

    def __str__(self):
        """Devuelve el modo de registro configurado."""

        return str(self.type_option)


class EmailExtensionsTeacher(TimeStampedModel):
    """Dominio de correo asociado a la política de registro para docentes."""

    domain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Dominio de correo aplicado al registro o validacion de docentes.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el dominio de docente esta activo dentro de la politica de registro.",
    )
    option_register_email = models.ForeignKey(OptionRegisterEmailExtension, on_delete=models.CASCADE,
                                              related_name='email_teacher_option_register',
                                              help_text="Politica que define como se interpreta este dominio para docentes.")

    def __str__(self):
        """Devuelve el dominio configurado para docentes."""

        return str(self.domain)


class EmailExtensionsExpert(TimeStampedModel):
    """Dominio de correo asociado a la política de registro para expertos."""

    domain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Dominio de correo aplicado al registro o validacion de expertos colaboradores.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el dominio de experto esta activo dentro de la politica de registro.",
    )
    option_register_email = models.ForeignKey(OptionRegisterEmailExtension, on_delete=models.CASCADE,
                                              related_name='email_expert_option_register',
                                              help_text="Politica que define como se interpreta este dominio para expertos.")

    def __str__(self):
        """Devuelve el dominio configurado para expertos."""

        return str(self.domain)


class EmailExtensionsStudent(TimeStampedModel):
    """Dominio de correo asociado a la política de registro para estudiantes."""

    domain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Dominio de correo aplicado al registro o validacion de estudiantes.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el dominio de estudiante esta activo dentro de la politica de registro.",
    )
    option_register_email = models.ForeignKey(OptionRegisterEmailExtension, on_delete=models.CASCADE,
                                              related_name='email_student_option_register',
                                              help_text="Politica que define como se interpreta este dominio para estudiantes.")

    def __str__(self):
        """Devuelve el dominio configurado para estudiantes."""

        return str(self.domain)


class UserTypeWithOption(TimeStampedModel):    
    """Relaciona un tipo de usuario con su política de registro por dominio.

    Esta tabla permite decidir, por descripción de rol o tipo de usuario, que
    opción de `OptionRegisterEmailExtension` debe aplicarse durante el alta.
    """


    description = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tipo de usuario o rol al que se asocia una politica de registro por dominio.",
    )
    option_register = models.ForeignKey(
        OptionRegisterEmailExtension,
        on_delete=models.CASCADE,
        related_name="user_type_option_register",
        help_text="Politica de dominios que aplica al tipo de usuario.",
    )

    def __str__(self):
        """Devuelve la descripción del tipo de usuario configurado."""

        return str(self.description)
