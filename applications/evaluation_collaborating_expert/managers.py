
"""Managers reutilizables para evaluación colaborativa experta."""

from django.db import models

class EvaluationExpertManager(models.Manager):
    """Agrupa consultas simples sobre evaluaciones expertas."""

    def rating_by_learningObject(self, oa_id):
        """Filtra evaluaciones asociadas a un objeto de aprendizaje concreto."""
        return self.filter(learning_object_id=oa_id)
