"""Permisos reutilizables del módulo `user`.

Este archivo encapsula las reglas de acceso por perfil activo para vistas DRF.
El proyecto distingue entre la existencia de un perfil relacionado y su estado
operativo (`is_active`), por eso cada permiso valida ambas cosas antes de dar
acceso.
"""

from rest_framework import permissions


class IsStudentUser(permissions.BasePermission):
    """Permite acceso solo a usuarios con perfil estudiante activo."""

    def has_permission(self, request, view):
        return bool(
            request.user.student is not None
            and bool(request.user and request.user.student.is_active)
        )


class IsGeneralUser(permissions.BasePermission):
    """Permite acceso a student, teacher o expert si el perfil esta activo."""

    def has_permission(self, request, view):
        student_active = (
            request.user.student is not None
            and bool(request.user and request.user.student.is_active)
        )
        teacher_active = (
            request.user.teacher is not None
            and bool(request.user and request.user.teacher.is_active)
        )
        expert_active = (
            request.user.collaboratingExpert is not None
            and bool(request.user and request.user.collaboratingExpert.is_active)
        )
        return bool(student_active or teacher_active or expert_active)


class IsTeacherUser(permissions.BasePermission):
    """Permite acceso solo a usuarios con perfil docente activo."""

    def has_permission(self, request, view):
        return bool(
            request.user.teacher is not None
            and bool(request.user and request.user.teacher.is_active)
        )


class IsCollaboratingExpertUser(permissions.BasePermission):
    """Permite acceso solo a usuarios con perfil experto colaborador activo."""

    def has_permission(self, request, view):
        if request.user != "AnonymousUser":
            return bool(
                request.user.collaboratingExpert is not None
                and (request.user and request.user.collaboratingExpert.is_active)
            )
        return False


class IsAdministratorUser(permissions.BasePermission):
    """Permite acceso a administradores activos y a super usuarios."""

    def has_permission(self, request, view):
        administrator_active = (
            request.user.administrator is not None
            and bool(request.user and request.user.administrator.is_active)
        )
        superuser_active = bool(request.user and request.user.is_superuser)
        return bool(administrator_active or superuser_active)
