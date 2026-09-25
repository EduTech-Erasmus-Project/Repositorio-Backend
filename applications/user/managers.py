"""Managers del módulo `user`.

Este manager centraliza la fábrica de cuentas base del proyecto. Aunque hoy la
asignación de perfiles (`Student`, `Teacher`, `CollaboratingExpert`,
`Administrator`) se completa en vistas y serializers, la creación de la cuenta
`User` y sus variantes históricas sigue viviendo aquí.
"""

from typing import Any

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Manager principal para crear cuentas `User` según el flujo requerido."""

    def create_user(self, email, first_name, last_name, password=None, *args: Any, **kwargs: Any):
        """Crea la cuenta base normalizando email y encriptando la contraseña."""

        if email is None:
            raise TypeError('El usuario debe tener un correo')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        """Crea una cuenta de super usuario sobre la fábrica base."""

        if password is None:
            raise TypeError('La contraseña no puede ser nulo')
        user = self.create_user(
            email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_admin_user(self, email, first_name, last_name, password):
        """Crea una cuenta destinada a enlazarse con el perfil administrador."""

        if password is None:
            raise TypeError('La contraseña no puede ser nulo')
        user = self.create_user(
            email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.save(using=self._db)
        return user

    def create_general_user(self, email, first_name, last_name, password):
        """Crea la cuenta base usada por student, teacher y expert."""

        if password is None:
            raise TypeError('La contraseña no puede ser nulo')
        user = self.create_user(
            email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.is_admin = False
        user.save(using=self._db)
        return user

    def create_student(self, email, first_name, last_name, password, *args, **kwargs):
        """Mantiene la fábrica heredada de cuentas orientadas a estudiante."""

        if password is None:
            raise TypeError('La contraseña no puede ser nulo')
        user = self.create_user(
            email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            *args,
            **kwargs
        )
        user.is_admin = False
        user.save(using=self._db)
        return user

    def user_filter_role(self, role):
        """Filtra usuarios por descripción de rol y ordena por creacion."""

        return self.filter(
            roles__description__contains=role,
        ).order_by("-created")

    def user_number_filter_role(self, role):
        """Devuelve el queryset base para conteos por descripción de rol."""

        return self.filter(
            roles__description__contains=role
        )
