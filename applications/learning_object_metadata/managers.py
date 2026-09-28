"""Managers y helpers de consulta para metadata de objetos de aprendizaje.

Este manager centraliza filtros reutilizados por vistas del módulo, sobre todo
los relacionados con propiedad del OA, visibilidad publica y accesos por slug.
"""

from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404


class LearningObjectManager(models.Manager):
    """Consultas reutilizables para metadata de objetos de aprendizaje."""

    def learning_object_metadata_by_user(self, user):
        """Lista los OAs visibles del usuario propietario."""

        return self.filter(
            user_created=user
        ).exclude(public=False).order_by("-pk")

    def learning_object_metadata_by_user_destroy(self, user, pk):
        """Elimina un OA solo si pertenece al usuario propietario indicado."""

        return self.filter(
            Q(user_created=user) and Q(pk=pk)
        ).delete()

    def learning_object_metadata_retrieve_by_user(self, user, pk):
        """Recupera un OA del propietario o lanza 404 si no coincide."""

        return get_object_or_404(
            self.filter(
                user_created=user
            ).order_by("-pk"),
            pk=pk,
        )

    def learningobjectBySlug(self, slug):
        """Busca OAs por slug para el endpoint publico de detalle."""

        return self.filter(
            slug=slug
        )

    def learning_object_by_knowledge_area(self, knowledge_area):
        """Filtra OAs publicos por area de conocimiento."""

        return self.filter(
            knowledge_area__name__contains=knowledge_area
        ).exclude(public=False).order_by("-created")

    def get_all_learning_objects(self):
        """Cuenta cuantos OAs públicos existen en el catálogo."""

        return self.filter(public=True).count()

    def get_learning_objects(self):
        """Devuelve los OAs públicos usados por recommendation system."""

        return self.filter(public=True).order_by("pk")
