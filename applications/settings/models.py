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
    host = models.CharField(max_length=300, null=True, blank=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    password = models.CharField(max_length=256, null=True)
    port = models.CharField(max_length=20, null=True, blank=True)
    tls = models.BooleanField(default=True)
    email_from = models.EmailField(null=True, blank=True)

    def __str__(self):
        return str(self.email_from)

    def decrypt_password(self):
        try:
            #pas = base64.urlsafe_b64decode(self.password)
            pas = self.password.encode('utf-8')
            cipher_pass = Fernet(env('HASH_KEY'))
            decode_pass = cipher_pass.decrypt(pas).decode("utf-8")
            return decode_pass
        except Exception as e:
            raise e

    def encrypt_password(self, password):
        try:
            pas = str(password).encode()
            cipher_pass = Fernet(env('HASH_KEY'))
            encrypt_pass = cipher_pass.encrypt(pas)
            return encrypt_pass
        except Exception as e:
            raise e


class OptionRegisterEmailExtension(TimeStampedModel):
    TYPE_CHOICES_OPTION = (
        ('ALL', 'ALL'),
        ('EXCEPT', 'EXCEPT'),
        ('ONLY', 'ONLY'),
    )
    type_option = models.CharField(max_length=40, choices=TYPE_CHOICES_OPTION, blank=True, null=True)

    def __str__(self):
        return str(self.type_option)


class EmailExtensionsTeacher(TimeStampedModel):

    domain = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    option_register_email = models.ForeignKey(OptionRegisterEmailExtension, on_delete=models.CASCADE,
                                              related_name='email_teacher_option_register')

    def __str__(self):
        return str(self.domain)


class EmailExtensionsExpert(TimeStampedModel):

    domain = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    option_register_email = models.ForeignKey(OptionRegisterEmailExtension, on_delete=models.CASCADE,
                                              related_name='email_expert_option_register')

    def __str__(self):
        return str(self.domain)


class EmailExtensionsStudent(TimeStampedModel):

    domain = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    option_register_email = models.ForeignKey(OptionRegisterEmailExtension, on_delete=models.CASCADE,
                                              related_name='email_student_option_register')

    def __str__(self):
        return str(self.domain)


class UserTypeWithOption(TimeStampedModel):
    description = models.CharField(max_length=50, unique=True)
    option_register = models.ForeignKey(OptionRegisterEmailExtension, on_delete=models.CASCADE, related_name="user_type_option_register")

    def __str__(self):
        return str(self.description)