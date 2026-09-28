"""Pruebas unitarias puras para `DataSetGenerator`.

Este archivo no toca endpoints ni base real. Se concentra en los helpers que
arman datasets intermedios para el recommendation system y valida:
- forma esperada de los dataframes cuando las consultas traen datos
- degradación a estructuras vacías cuando no hay datos
- manejo seguro de errores de consulta sin propagar excepciones
"""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.db import DatabaseError
from django.test import SimpleTestCase

from applications.recommendation_system.dataset_generator import DataSetGenerator


class _ValuesResult:
    """Stub mínimo que imita el resultado encadenable de `.values()` en el ORM."""

    def __init__(self, rows):
        """Guarda las filas simuladas que luego expondrá el stub."""
        self.rows = rows

    def __iter__(self):
        """Permite iterar las filas como si fueran un resultado real del ORM."""
        return iter(self.rows)

    def order_by(self, *args, **kwargs):
        """Mantiene la cadena de llamadas devolviendo la misma instancia."""
        return self

    def __getitem__(self, item):
        """Soporta indexación para helpers que acceden por posición."""
        return self.rows[item]


class RecommendationDatasetGeneratorGuardTests(SimpleTestCase):
    """Pruebas puras para los helpers pequeños que alimentan el recommendation endpoint."""

    def setUp(self):
        """Crea el generador y un usuario mínimo para los helpers que lo requieren."""
        self.generator = DataSetGenerator()
        self.user = SimpleNamespace(id=99)

    @patch("applications.recommendation_system.dataset_generator.EvaluationQuestion.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationQuestionsQualification.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationConceptQualification.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationCollaboratingExpert.objects.all")
    def test_learning_object_question_dataset_returns_grouped_dataframe(
        self, mock_oa_all, mock_concept_qualifications_all, mock_question_qualifications_all, mock_questions_all
    ):
        """Agrupa calificaciones por pregunta y devuelve el dataframe esperado."""
        oa_qs = Mock()
        oa_qs.values.return_value = [
            {"id": 1, "learning_object": 39},
        ]
        mock_oa_all.return_value = oa_qs

        concept_qualifications_qs = Mock()
        concept_qualifications_qs.values.return_value = [
            {"id": 100, "evaluation_collaborating_expert": 1},
            {"id": 101, "evaluation_collaborating_expert": 1},
        ]
        mock_concept_qualifications_all.return_value = concept_qualifications_qs

        question_qualifications_qs = Mock()
        question_qualifications_qs.values.return_value = [
            {"id": 201, "concept_evaluations": 100, "evaluation_question": 7, "qualification": 1.2},
            {"id": 202, "concept_evaluations": 101, "evaluation_question": 7, "qualification": 1.8},
            {"id": 203, "concept_evaluations": 100, "evaluation_question": 8, "qualification": 0.6},
        ]
        mock_question_qualifications_all.return_value = question_qualifications_qs

        questions_qs = Mock()
        questions_qs.values.return_value = [
            {"id": 7, "description": "Pregunta 1", "schema": "Schema 1", "code": "Q1"},
            {"id": 8, "description": "Pregunta 2", "schema": "Schema 2", "code": "Q2"},
        ]
        mock_questions_all.return_value = questions_qs

        result = self.generator.learning_object_question_dataset()

        self.assertEqual(result.columns.tolist(), ["oaId", "code", "qualification"])
        self.assertEqual(result["oaId"].tolist(), [39, 39])
        self.assertEqual(result["code"].tolist(), ["Q1", "Q2"])
        self.assertEqual(result["qualification"].tolist(), [2, 1])

    @patch("applications.recommendation_system.dataset_generator.EvaluationQuestion.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationQuestionsQualification.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationConceptQualification.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationCollaboratingExpert.objects.all")
    def test_learning_object_question_dataset_returns_empty_dataframe_when_sources_are_empty(
        self, mock_oa_all, mock_concept_qualifications_all, mock_question_qualifications_all, mock_questions_all
    ):
        """Si todas las fuentes están vacías, el helper debe devolver dataframe vacío."""
        oa_qs = Mock()
        oa_qs.values.return_value = []
        mock_oa_all.return_value = oa_qs

        concept_qualifications_qs = Mock()
        concept_qualifications_qs.values.return_value = []
        mock_concept_qualifications_all.return_value = concept_qualifications_qs

        question_qualifications_qs = Mock()
        question_qualifications_qs.values.return_value = []
        mock_question_qualifications_all.return_value = question_qualifications_qs

        questions_qs = Mock()
        questions_qs.values.return_value = []
        mock_questions_all.return_value = questions_qs

        result = self.generator.learning_object_question_dataset()

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), ["oaId", "code", "qualification"])

    @patch("applications.recommendation_system.dataset_generator.EvaluationCollaboratingExpert.objects.all")
    def test_learning_object_question_dataset_returns_empty_dataframe_when_query_fails(self, mock_oa_all):
        """Si falla la consulta principal, el helper debe degradar a dataframe vacío."""
        mock_oa_all.side_effect = DatabaseError("boom")

        result = self.generator.learning_object_question_dataset()

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), ["oaId", "code", "qualification"])

    @patch("applications.recommendation_system.dataset_generator.EvaluationConcept.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationConceptQualification.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationCollaboratingExpert.objects.filter")
    def test_learning_object_concept_dataset_returns_grouped_dataframe(
        self, mock_oa_filter, mock_qualifications_all, mock_concepts_all
    ):
        """Agrupa promedios por concepto y OA usando solo evaluaciones de OAs públicos."""
        oa_qs = Mock()
        oa_qs.values.return_value = [
            {"id": 1, "learning_object": 39},
            {"id": 2, "learning_object": 46},
        ]
        mock_oa_filter.return_value = oa_qs

        qualifications_qs = Mock()
        qualifications_qs.values.return_value = [
            {"id": 11, "evaluation_concept": 1, "evaluation_collaborating_expert": 1, "average": 1.0},
            {"id": 12, "evaluation_concept": 1, "evaluation_collaborating_expert": 1, "average": 2.0},
            {"id": 13, "evaluation_concept": 2, "evaluation_collaborating_expert": 2, "average": 1.5},
        ]
        mock_qualifications_all.return_value = qualifications_qs

        concepts_qs = Mock()
        concepts_qs.values.return_value = [
            {"id": 1, "concept": "Recursos Digitales Visuales"},
            {"id": 2, "concept": "Recursos Digitales Auditivos"},
        ]
        mock_concepts_all.return_value = concepts_qs

        result = self.generator.learning_object_concept_dataset()

        mock_oa_filter.assert_called_once_with(learning_object__public=True)
        self.assertEqual(result.columns.tolist(), ["oaId", "concept", "average"])
        self.assertEqual(result["oaId"].tolist(), [39, 46])
        self.assertEqual(result["concept"].tolist(), ["Recursos Digitales Visuales", "Recursos Digitales Auditivos"])
        self.assertEqual(result["average"].tolist(), [1.5, 1.5])

    @patch("applications.recommendation_system.dataset_generator.EvaluationConcept.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationConceptQualification.objects.all")
    @patch("applications.recommendation_system.dataset_generator.EvaluationCollaboratingExpert.objects.filter")
    def test_learning_object_concept_dataset_returns_empty_dataframe_when_sources_are_empty(
        self, mock_oa_filter, mock_qualifications_all, mock_concepts_all
    ):
        """Si no hay evaluaciones ni conceptos, el helper debe devolver dataframe vacío."""
        oa_qs = Mock()
        oa_qs.values.return_value = []
        mock_oa_filter.return_value = oa_qs

        qualifications_qs = Mock()
        qualifications_qs.values.return_value = []
        mock_qualifications_all.return_value = qualifications_qs

        concepts_qs = Mock()
        concepts_qs.values.return_value = []
        mock_concepts_all.return_value = concepts_qs

        result = self.generator.learning_object_concept_dataset()

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), ["oaId", "concept", "average"])

    @patch("applications.recommendation_system.dataset_generator.EvaluationCollaboratingExpert.objects.filter")
    def test_learning_object_concept_dataset_returns_empty_dataframe_when_query_fails(self, mock_oa_filter):
        """Si falla la consulta de evaluaciones, la salida debe quedar vacía."""
        mock_oa_filter.side_effect = DatabaseError("boom")

        result = self.generator.learning_object_concept_dataset()

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), ["oaId", "concept", "average"])

    @patch("applications.recommendation_system.dataset_generator.PreferencesArea.objects.all")
    @patch("applications.recommendation_system.dataset_generator.Preferences.objects.all")
    @patch("applications.recommendation_system.dataset_generator.Student.objects.filter")
    def test_user_profile_dataset_returns_expected_dataframe(self, mock_filter, mock_preferences_all, mock_pref_areas_all):
        """Construye el dataframe del perfil del usuario con banderas y puntajes esperados."""
        user = SimpleNamespace(id=99, student=SimpleNamespace(id=7))

        student_qs = Mock()
        student_qs.values.return_value = [
            {"id": 7, "preferences": 1},
            {"id": 7, "preferences": 3},
        ]
        mock_filter.return_value = student_qs

        preferences_qs = Mock()
        preferences_qs.values.return_value = [
            {"id": 1, "description": "Texto", "priority": 0.8, "preferences_area": 1},
            {"id": 2, "description": "Audio", "priority": 0.3, "preferences_area": 2},
            {"id": 3, "description": "Color", "priority": 0.5, "preferences_area": 1},
        ]
        mock_preferences_all.return_value = preferences_qs

        pref_areas_qs = Mock()
        pref_areas_qs.values.return_value = [
            {"id": 1, "preferences_are": "Visual"},
            {"id": 2, "preferences_are": "Auditory"},
        ]
        mock_pref_areas_all.return_value = pref_areas_qs

        result = self.generator.user_profile_dataset(user)

        self.assertEqual(
            result.columns.tolist(),
            ["preferences_are", "preferences", "myPref", "priority", "Total"],
        )
        self.assertEqual(result["preferences_are"].tolist(), ["Visual", "Auditory", "Visual"])
        self.assertEqual(result["myPref"].tolist(), [1, 0, 1])
        self.assertEqual(result["Total"].tolist(), [0.8, 0.0, 0.5])

    def test_user_profile_dataset_returns_empty_dataframe_when_user_has_no_student_profile(self):
        """Sin perfil de estudiante el helper debe responder con dataframe vacío."""
        result = self.generator.user_profile_dataset(SimpleNamespace(id=99))

        self.assertTrue(result.empty)
        self.assertEqual(
            result.columns.tolist(),
            ["preferences_are", "preferences", "myPref", "priority", "Total"],
        )

    @patch("applications.recommendation_system.dataset_generator.Student.objects.filter")
    def test_user_profile_dataset_returns_empty_dataframe_when_query_fails(self, mock_filter):
        """Si falla la consulta del estudiante, la salida debe mantenerse vacía."""
        user = SimpleNamespace(id=99, student=SimpleNamespace(id=7))
        mock_filter.side_effect = DatabaseError("boom")

        result = self.generator.user_profile_dataset(user)

        self.assertTrue(result.empty)
        self.assertEqual(
            result.columns.tolist(),
            ["preferences_are", "preferences", "myPref", "priority", "Total"],
        )

    @patch("applications.recommendation_system.dataset_generator.Interaction.objects.filter")
    def test_learning_object_view_returns_learning_object_ids(self, mock_filter):
        """Extrae solo los IDs de OAs vistos a partir de las interacciones del usuario."""
        qs = Mock()
        qs.values.return_value = _ValuesResult(
            [
                {"id": 1, "learning_object": 10},
                {"id": 2, "learning_object": 20},
            ]
        )
        mock_filter.return_value = qs

        result = self.generator.LearningObjectView(self.user)

        self.assertEqual(result, [10, 20])

    @patch("applications.recommendation_system.dataset_generator.Interaction.objects.filter")
    def test_learning_object_view_returns_empty_when_query_fails(self, mock_filter):
        """Si falla la consulta de vistas, el helper debe devolver lista vacía."""
        mock_filter.side_effect = DatabaseError("boom")

        result = self.generator.LearningObjectView(self.user)

        self.assertEqual(result, [])

    @patch("applications.recommendation_system.dataset_generator.Interaction.objects.filter")
    def test_user_learning_object_liked_returns_dataframe_without_id_and_with_int_liked(self, mock_filter):
        """Normaliza el dataset de likes quitando `id` y convirtiendo `liked` a entero."""
        qs = Mock()
        qs.values.return_value = _ValuesResult(
            [
                {"user": 99, "id": 7, "learning_object": 39, "liked": True},
            ]
        )
        mock_filter.return_value = qs

        result = self.generator.user_learning_object_liked(self.user)

        self.assertEqual(result.columns.tolist(), ["user", "learning_object", "liked"])
        self.assertEqual(result.iloc[0]["learning_object"], 39)
        self.assertEqual(result.iloc[0]["liked"], 1)

    @patch("applications.recommendation_system.dataset_generator.Interaction.objects.filter")
    def test_user_learning_object_liked_returns_empty_dataframe_when_query_fails(self, mock_filter):
        """Si falla la consulta de likes, debe devolver un dataframe vacío tipado."""
        mock_filter.side_effect = DatabaseError("boom")

        result = self.generator.user_learning_object_liked(self.user)

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), ["user", "learning_object", "liked"])

    @patch("applications.recommendation_system.dataset_generator.LearningObjectMetadata.objects.filter")
    def test_learning_object_metadata_returns_dataframe_with_expected_columns(self, mock_filter):
        """Devuelve metadata publica con las columnas que usa la recomendación TF-IDF."""
        qs = Mock()
        qs.values.return_value = [
            {"id": 39, "general_keyword": "python basico", "general_title": "OA Python"},
        ]
        mock_filter.return_value = qs

        result = self.generator.learning_object_metadata()

        mock_filter.assert_called_once_with(public=True)
        self.assertEqual(result.columns.tolist(), ["id", "general_keyword", "general_title"])
        self.assertEqual(result.iloc[0]["id"], 39)

    @patch("applications.recommendation_system.dataset_generator.LearningObjectMetadata.objects.filter")
    def test_learning_object_metadata_returns_empty_dataframe_when_query_fails(self, mock_filter):
        """Si falla la consulta de metadata pública, la salida debe quedar vacía."""
        mock_filter.side_effect = DatabaseError("boom")

        result = self.generator.learning_object_metadata()

        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), ["id", "general_keyword", "general_title"])
