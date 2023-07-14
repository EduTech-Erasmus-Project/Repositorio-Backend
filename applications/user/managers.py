from django.contrib.auth.models import BaseUserManager
from django.db import models
from typing import Any
class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password = None,*args: Any, **kwargs: Any):
        if email is None:
            raise TypeError('El usuario debe tener un correo')

        user = self.model(
            email = self.normalize_email(email), 
            first_name=first_name, 
            last_name=last_name,
            )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, first_name, last_name, password):
        if password is None:
            raise TypeError('Lacontraseña no puede ser nulo')
        user = self.create_user(
            email, 
            first_name= first_name, 
            last_name= last_name,
            password= password
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_admin_user(self, email, first_name, last_name, password):
        if password is None:
            raise TypeError('Lacontraseña no puede ser nulo')
        user = self.create_user(
            email, 
            first_name= first_name, 
            last_name= last_name,
            password= password
        )
        user.save(using=self._db)
        return user

    def create_general_user(self, email, first_name, last_name, password):
        if password is None:
            raise TypeError('Lacontraseña no puede ser nulo')
        user = self.create_user(
            email, 
            first_name= first_name, 
            last_name= last_name,
            password= password
        )
        user.is_admin = False
        user.save(using=self._db)
        return user
        
    def create_student(self, email, first_name, last_name, password,*args, **kwargs):
        if password is None:
            raise TypeError('Lacontraseña no puede ser nulo')
        user = self.create_user(
            email, 
            first_name= first_name, 
            last_name= last_name,
            password= password,
            *args,
            **kwargs
        )
        user.is_admin = False
        user.save(using=self._db)
        return user

    def user_filter_role(self,role):
        return self.filter(
            roles__description__contains=role,
        ).order_by("-created")

    def user_number_filter_role(self,role):
        return self.filter(
            roles__description__contains=role
        )
    
    # def create_user_student(self, username, email, first_name, last_name, password):
    #     if password is None:
    #         raise TypeError('Lacontraseña no puede ser nulo')
    #     user = self.create_user(
    #         username, 
    #         email=email, 
    #         first_name= first_name, 
    #         last_name= last_name,
    #         password= password
    #     )
    #     user.is_student = True
    #     user.save(using=self._db)
    #     return user
    # def create_user_student(self,username, email, first_name, last_name, password = None,**extra_fields):
    #     if username is None:
    #         raise TypeError('El usuario debe tener nombre de usuario')
    #     if email is None:
    #         raise TypeError('El usuario debe tener un correo')

    #     # user = self.model(username=username, email = self.normalize_email(email), first_name=first_name, last_name=last_name)
    #     # user.set_password(password)
    #     # user.save(using=self._db)
    #     return self.create_user(username,email,first_name,last_name, password)