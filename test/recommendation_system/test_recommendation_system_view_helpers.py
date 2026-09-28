"""Pruebas puras para los helpers defensivos de `LearningObjectRecommended`.

Esta suite no usa base de datos. Se concentra en la parte de la vista que:
- combina liked, vistos y recomendados
- transforma el perfil del usuario
- degrada a `[]` cuando algun dataset viene incompleto o una dependencia falla

Sirve para documentar el comportamiento actual de los guards del queryset final.
"""

import pandas as pd
from django.test import SimpleTestCase
from unittest.mock import Mock, patch

from applications.recommendation_system import views as recommendation_views


class RecommendationViewHelperGuardTests(SimpleTestCase):
    """Pruebas puras para helpers defensivos del recommendation system."""

    def setUp(self):
        """Crea una instancia de la vista con un `request.user` mínimo simulado."""
        self.view = recommendation_views.LearningObjectRecommended()
        self.view.request = Mock(user=Mock(id=99))

    def _build_preferences_dataframe(self):
        """Construye el dataframe mínimo valido del perfil de preferencias."""
        return pd.DataFrame(
            [
                {"preferences_are": "Nivel De Interactividad", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Auditivos", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Textuales", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Visuales", "priority": 1, "Total": 2},
            ]
        )

    def test_recomended_keeps_current_happy_path(self):
        """Mantiene la regla actual cuando el dataset viene bien formado."""
        df_oa = pd.DataFrame(
            [
                {"oaId": 1, "concept": "Nivel De Interactividad", "average": 1.0},
                {"oaId": 1, "concept": "Recursos Digitales Auditivos", "average": 1.0},
                {"oaId": 1, "concept": "Recursos Digitales Textuales", "average": 1.0},
                {"oaId": 1, "concept": "Recursos Digitales Visuales", "average": 1.0},
                {"oaId": 2, "concept": "Nivel De Interactividad", "average": 1.0},
                {"oaId": 2, "concept": "Recursos Digitales Auditivos", "average": 1.0},
                {"oaId": 2, "concept": "Recursos Digitales Textuales", "average": 0.25},
                {"oaId": 2, "concept": "Recursos Digitales Visuales", "average": 1.0},
            ]
        )
        df_user = [
            {"Nivel De Interactividad": 0.5},
            {"Recursos Digitales Auditivos": 0.5},
            {"Recursos Digitales Textuales": 0.5},
            {"Recursos Digitales Visuales": 0.5},
        ]

        result = self.view.recomended(df_oa, df_user)

        self.assertEqual(result, [1])

    def test_recomended_returns_empty_when_required_columns_are_missing(self):
        """Si faltan columnas requeridas, no debe explotar ni devolver Exception."""
        df_oa = pd.DataFrame(
            [
                {"oaId": 1, "concept": "Nivel De Interactividad"},
            ]
        )
        df_user = [
            {"Nivel De Interactividad": 0.5},
            {"Recursos Digitales Auditivos": 0.5},
            {"Recursos Digitales Textuales": 0.5},
            {"Recursos Digitales Visuales": 0.5},
        ]

        result = self.view.recomended(df_oa, df_user)

        self.assertEqual(result, [])

    def test_recomended_returns_empty_when_user_profile_is_short(self):
        """Si el perfil del usuario no trae las 4 áreas, el helper responde vacío."""
        df_oa = pd.DataFrame(
            [
                {"oaId": 1, "concept": "Nivel De Interactividad", "average": 1.0},
            ]
        )
        df_user = [
            {"Nivel De Interactividad": 0.5},
        ]

        result = self.view.recomended(df_oa, df_user)

        self.assertEqual(result, [])

    def test_get_user_preferences_value_returns_empty_when_inputs_are_invalid(self):
        """Si los insumos no son Series-like, no debe devolver Exception."""
        result = self.view.get_user_preferences_value(totalByUser=None, priority=None)

        self.assertEqual(result, [])

    @patch.object(recommendation_views.EvaluationCollaboratingExpert.objects, "filter")
    @patch.object(recommendation_views.LearningObjectRecommended, "recomended", return_value=[30, 20])
    @patch.object(
        recommendation_views.dataset_generator,
        "learning_object_concept_dataset",
        return_value=pd.DataFrame(),
    )
    @patch.object(
        recommendation_views.dataset_generator,
        "user_profile_dataset",
        return_value=pd.DataFrame(
            [
                {"preferences_are": "Nivel De Interactividad", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Auditivos", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Textuales", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Visuales", "priority": 1, "Total": 2},
            ]
        ),
    )
    @patch.object(recommendation_views.dataset_generator, "LearningObjectView", return_value=[20])
    @patch.object(recommendation_views.recommended, "user_learning_object_recomended_liked", return_value=[10, 20])
    def test_get_queryset_keeps_happy_path_with_mocked_dependencies(
        self,
        _mock_liked,
        _mock_viewed,
        _mock_profile,
        _mock_dataset,
        _mock_recomended,
        mock_filter,
    ):
        """Mantiene la union liked+expert y excluye OAs ya vistos antes del queryset final."""

        class QueryChain:
            """Stub mínimo para encadenar `filter().order_by().distinct()` en la vista."""

            def __init__(self, result):
                """Guarda el resultado final que devolverá la cadena simulada."""
                self.result = result

            def order_by(self, *args, **kwargs):
                """Devuelve la misma cadena para imitar el queryset real."""
                return self

            def distinct(self, *args, **kwargs):
                """Mantiene la cadena sin modificar el resultado simulado."""
                return self

            def __getitem__(self, item):
                """Entrega el resultado final cuando la vista corta el queryset."""
                return self.result

        mock_filter.return_value = QueryChain(["ok"])

        result = self.view.get_queryset()

        self.assertEqual(result, ["ok"])
        self.assertEqual(set(mock_filter.call_args.kwargs["learning_object__id__in"]), {10, 30})

    @patch.object(
        recommendation_views.dataset_generator,
        "user_profile_dataset",
        return_value=object(),
    )
    @patch.object(recommendation_views.dataset_generator, "LearningObjectView", return_value=[])
    @patch.object(recommendation_views.recommended, "user_learning_object_recomended_liked", return_value=[10])
    def test_get_queryset_returns_empty_when_profile_dataset_is_invalid(
        self, _mock_liked, _mock_viewed, _mock_profile
    ):
        """Si el dataset de preferencias viene mal formado, el queryset debe caer a lista vacía."""
        result = self.view.get_queryset()

        self.assertEqual(result, [])

    @patch.object(
        recommendation_views.recommended,
        "user_learning_object_recomended_liked",
        side_effect=RuntimeError("boom"),
    )
    def test_get_queryset_returns_empty_when_dependency_raises_runtime_error(self, _mock_liked):
        """Mantiene el contrato actual de devolver [] si una dependencia interna explota."""
        result = self.view.get_queryset()

        self.assertEqual(result, [])
