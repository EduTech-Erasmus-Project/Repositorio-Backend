import re
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions

class IsStudentUser(permissions.BasePermission):
    """
    Allows access only to student users.
    """
    def  has_permission(self, request, view):
        return bool(request.user.student is not None and bool(request.user and request.user.student.is_active))
# class IsGeneralUser(LoginRequiredMixin):
class IsGeneralUser(permissions.BasePermission):
    """
    Access teacher, student, collaboratingExpert.
    """
    def  has_permission(self, request, view):
        if (request.user.student is not None and bool(request.user and request.user.student.is_active)) or (request.user.teacher is not None and bool(request.user and request.user.teacher.is_active)or (request.user.collaboratingExpert is not None and bool(request.user and request.user.collaboratingExpert.is_active))) :
            return True
        else:
            return False
class IsTeacherUser(permissions.BasePermission):
    """
    Allows access only to teacher users.
    """
    def has_permission(self, request, view):
        return bool(request.user.teacher is not None and bool(request.user and request.user.teacher.is_active))

class IsCollaboratingExpertUser(permissions.BasePermission):
    """
    Allows access only to collaborating expert users.
    """
    def has_permission(self, request, view):
        if(request.user != "AnonymousUser"):
            return bool(request.user.collaboratingExpert is not None and (request.user and request.user.collaboratingExpert.is_active))

class IsAdministratorUser(permissions.BasePermission):
    """
    Allows access only to administrator expert users.
    """
    def  has_permission(self, request, view):
        # if request.user == 'AnonymousUser':
        #     return False
        if (request.user.administrator is not None and bool(request.user and request.user.administrator.is_active) or bool(request.user and request.user.is_superuser)):
            return True
        else:
            return False
            