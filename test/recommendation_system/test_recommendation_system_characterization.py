"""Pruebas de caracterización del recommendation system.

Este bloque mezcla dos niveles de prueba:
- una suite con base de datos y endpoint real para describir que expone hoy
  `/api/v1/learning-objects/recommended/`
- una suite de helpers puros para dejar fijas reglas internas del algoritmo,
  como el orden de preferencias y el tratamiento de datasets incompletos

La palabra clave aqui es "caracterización": estas pruebas describen el
comportamiento actual, incluso cuando ese comportamiento es defensivo o legado.
"""

import io
import shutil
from unittest.mock import Mock, patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.recommendation_system import recommended as recommendation_recommended
from applications.recommendation_system import views as recommendation_views
from applications.user.models import CollaboratingExpert, Student, Teacher
from test.helpers.temp_media_root import build_test_media_root


class RecommendationEndpointCharacterizationTests(TestCase):
    """Caracteriza el endpoint publico/autenticado de recomendaciones."""

    def setUp(self):
        """Prepara usuarios y OAs minimos para probar la respuesta del endpoint."""
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-recommendation-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.teacher_user = self._create_teacher_user()
        self.student_user = self._create_student_user()
        self.expert_user = self._create_expert_user()
        self._sequence = 0

        self.level = EducationLevel.objects.create(
            name_es="Nivel Recommendation",
            name_en="Recommendation Level",
        )
        self.area = KnowledgeArea.objects.create(
            name_es="Area Recommendation",
            description_es="Desc",
            name_en="Recommendation Area",
            description_en="Desc",
        )
        self.license = License.objects.create(
            name_es="Licencia Recommendation",
            name_en="Recommendation License",
            value="RECOMMENDATION-LICENSE",
        )

        self.oa_one = self._create_learning_object_metadata("OA Recommendation 1")
        self.oa_two = self._create_learning_object_metadata("OA Recommendation 2")
        self.oa_three = self._create_learning_object_metadata("OA Recommendation 3")

        self._create_expert_evaluation(self.oa_one, 1.0)
        self._create_expert_evaluation(self.oa_two, 1.5)
        self._create_expert_evaluation(self.oa_three, 2.0)

    def tearDown(self):
        """Limpia MEDIA_ROOT temporal del módulo de recommendation."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _build_avatar_png(self):
        """Genera un avatar mínimo valido para los OAs de prueba."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-recommendation.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _create_teacher_user(self):
        """Crea un docente activo para ser propietario de los OAs."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-recommendation@example.com",
            first_name="Teacher",
            last_name="Recommendation",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_student_user(self):
        """Crea un estudiante activo para consumir el endpoint."""
        student = Student.objects.create(
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-recommendation@example.com",
            first_name="Student",
            last_name="Recommendation",
            password="StrongPass123",
        )
        user.student = student
        user.save()
        return user

    def _create_expert_user(self):
        """Crea un experto activo que firma las evaluaciones usadas por el serializer."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Alto",
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="expert-recommendation@example.com",
            first_name="Expert",
            last_name="Recommendation",
            password="StrongPass123",
        )
        user.collaboratingExpert = expert
        user.save()
        return user

    def _create_learning_object_metadata(self, title):
        """Crea un OA minimo para serializarlo desde EvaluationCollaboratingExpert."""
        self._sequence += 1
        seq = self._sequence
        learning_object_file = LearningObjectFile.objects.create(
            file=SimpleUploadedFile(
                f"recommendation-{seq}.zip",
                b"PK\x03\x04",
                content_type="application/zip",
            ),
            url=f"http://testserver/media/catalog/recommendation-{seq}/index.html",
            file_name=f"recommendation-{seq}",
            file_size=1,
            path_origin=self.media_root,
        )
        return LearningObjectMetadata.objects.create(
            learning_object_file=learning_object_file,
            adaptation="none",
            avatar=self._build_avatar_png(),
            general_title=title,
            general_description=f"Descripcion de {title}",
            general_language="es",
            education_levels=self.level,
            knowledge_area=self.area,
            license=self.license,
            user_created=self.teacher_user,
            public=True,
        )

    def _create_expert_evaluation(self, learning_object, rating):
        """Crea la fila que realmente expone el endpoint recomendado."""
        return EvaluationCollaboratingExpert.objects.create(
            learning_object=learning_object,
            rating=rating,
            observation="Caracterizacion recommendation",
            collaborating_expert=self.expert_user,
        )

    def _build_preferences_dataframe(self):
        """Construye el dataset mínimo esperado por get_user_preferences_value."""
        return pd.DataFrame(
            [
                {"preferences_are": "Nivel De Interactividad", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Auditivos", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Textuales", "priority": 1, "Total": 2},
                {"preferences_are": "Recursos Digitales Visuales", "priority": 1, "Total": 2},
            ]
        )

    def test_recommended_endpoint_requires_authenticated_user(self):
        """Sin autenticación el endpoint no debe exponer recomendaciones."""
        response = self.client.get("/api/v1/learning-objects/recommended/")

        self.assertEqual(response.status_code, 401, response.data)

    def test_recommended_endpoint_unions_sources_and_excludes_viewed_objects(self):
        """Une liked+expert, excluye vistos y devuelve EvaluationCollaboratingExpert ordenado por OA."""
        self.client.force_authenticate(user=self.student_user)

        with patch.object(
            recommendation_views.recommended,
            "user_learning_object_recomended_liked",
            return_value=[self.oa_one.id, self.oa_two.id],
        ), patch.object(
            recommendation_views.dataset_generator,
            "LearningObjectView",
            return_value=[self.oa_two.id],
        ), patch.object(
            recommendation_views.dataset_generator,
            "user_profile_dataset",
            return_value=self._build_preferences_dataframe(),
        ), patch.object(
            recommendation_views.dataset_generator,
            "learning_object_concept_dataset",
            return_value=pd.DataFrame(),
        ), patch.object(
            recommendation_views.LearningObjectRecommended,
            "recomended",
            return_value=[self.oa_three.id, self.oa_two.id],
        ):
            response = self.client.get("/api/v1/learning-objects/recommended/")

        self.assertEqual(response.status_code, 200, response.data)
        recommended_ids = [item["learning_object"]["id"] for item in response.data]
        self.assertEqual(recommended_ids, [self.oa_three.id, self.oa_one.id])

    def test_recommended_endpoint_returns_empty_list_when_internal_error_occurs(self):
        """Caracteriza el comportamiento legacy: ante error interno, hoy responde lista vacia."""
        self.client.force_authenticate(user=self.student_user)

        with patch.object(
            recommendation_views.recommended,
            "user_learning_object_recomended_liked",
            side_effect=RuntimeError("boom"),
        ):
            response = self.client.get("/api/v1/learning-objects/recommended/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, [])

    def test_recommended_endpoint_returns_only_public_learning_objects(self):
        """Aunque las fuentes internas sugieran privados, el endpoint final no debe exponerlos."""
        private_oa = self._create_learning_object_metadata("OA Recommendation Private")
        private_oa.public = False
        private_oa.save(update_fields=["public"])
        self._create_expert_evaluation(private_oa, 3.0)

        self.client.force_authenticate(user=self.student_user)

        with patch.object(
            recommendation_views.recommended,
            "user_learning_object_recomended_liked",
            return_value=[self.oa_one.id, private_oa.id],
        ), patch.object(
            recommendation_views.dataset_generator,
            "LearningObjectView",
            return_value=[],
        ), patch.object(
            recommendation_views.dataset_generator,
            "user_profile_dataset",
            return_value=self._build_preferences_dataframe(),
        ), patch.object(
            recommendation_views.dataset_generator,
            "learning_object_concept_dataset",
            return_value=pd.DataFrame(),
        ), patch.object(
            recommendation_views.LearningObjectRecommended,
            "recomended",
            return_value=[private_oa.id],
        ):
            response = self.client.get("/api/v1/learning-objects/recommended/")

        self.assertEqual(response.status_code, 200, response.data)
        recommended_ids = [item["learning_object"]["id"] for item in response.data]
        self.assertIn(self.oa_one.id, recommended_ids)
        self.assertNotIn(private_oa.id, recommended_ids)


class RecommendationHelperCharacterizationTests(SimpleTestCase):
    """Caracteriza helpers puros del recommendation system sin tocar BD."""

    def test_get_user_preferences_value_preserves_current_fixed_area_order(self):
        """Documenta el orden rigido actual de las cuatro areas de preferencia."""
        view = recommendation_views.LearningObjectRecommended()

        result = view.get_user_preferences_value(
            pd.Series([1, 2, 3, 4]),
            pd.Series([2, 4, 6, 8]),
        )

        self.assertEqual(
            result,
            [
                {"Nivel De Interactividad": 4.0},
                {"Recursos Digitales Auditivos": 4.0},
                {"Recursos Digitales Textuales": 4.0},
                {"Recursos Digitales Visuales": 4.0},
            ],
        )

    def test_recomended_requires_all_four_concepts_to_meet_thresholds(self):
        """Caracteriza la regla actual: un OA entra solo si supera las 4 áreas fijas."""
        view = recommendation_views.LearningObjectRecommended()
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

        result = view.recomended(df_oa, df_user)

        self.assertEqual(result, [1])

    @patch.object(recommendation_recommended.dataset_generator, "learning_object_metadata")
    def test_learning_object_recomended_uses_loid_column_not_dataframe_position(self, mock_metadata):
        """Debe buscar el OA liked por columna loId aunque los IDs no sean consecutivos."""
        mock_metadata.return_value = pd.DataFrame(
            [
                {"id": 10, "general_keyword": "python basico", "general_title": "OA Python"},
                {"id": 42, "general_keyword": "robotica sensores", "general_title": "OA Robotica"},
                {"id": 77, "general_keyword": "python avanzado datos", "general_title": "OA Datos"},
            ]
        )

        result = recommendation_recommended.learning_object_recomended(42)

        self.assertEqual(result, [10, 77])

    @patch("applications.recommendation_system.recommended.learning_object_recomended")
    @patch.object(recommendation_recommended.dataset_generator, "user_learning_object_liked")
    def test_user_learning_object_recomended_liked_uses_first_scalar_id(self, mock_liked, mock_recommended):
        """Debe extraer el primer learning_object como escalar en vez de convertir la Series completa."""
        mock_liked.return_value = pd.DataFrame(
            [
                {"learning_object": 39, "liked": 1},
            ]
        )
        mock_recommended.return_value = [10, 77]

        result = recommendation_recommended.ItemsRecomended().user_learning_object_recomended_liked(
            user=Mock()
        )

        self.assertEqual(result, [10, 77])
        mock_recommended.assert_called_once_with(39)

    @patch.object(recommendation_recommended.dataset_generator, "user_learning_object_liked")
    def test_user_learning_object_recomended_liked_returns_empty_when_learning_object_column_is_missing(
        self, mock_liked
    ):
        """Si el dataset viene sin learning_object, el helper debe responder [] sin explotar."""
        mock_liked.return_value = pd.DataFrame(
            [
                {"liked": 1},
            ]
        )

        result = recommendation_recommended.ItemsRecomended().user_learning_object_recomended_liked(
            user=Mock()
        )

        self.assertEqual(result, [])

    @patch.object(recommendation_recommended.dataset_generator, "learning_object_metadata")
    def test_learning_object_recomended_returns_empty_when_required_columns_are_missing(self, mock_metadata):
        """Si faltan columnas esperadas del metadata dataset, debe responder [] en vez de romper."""
        mock_metadata.return_value = pd.DataFrame(
            [
                {"id": 42, "general_title": "OA Robotica"},
            ]
        )

        result = recommendation_recommended.learning_object_recomended(42)

        self.assertEqual(result, [])

    @patch("applications.recommendation_system.recommended.stopwords.words", side_effect=LookupError())
    def test_build_tfidf_vectorizer_falls_back_when_stopwords_resource_is_missing(self, _mock_words):
        """Si falta el recurso de NLTK, el vectorizador debe construirse sin descargar en import-time."""
        recommendation_recommended.get_spanish_stopwords.cache_clear()

        vectorizer = recommendation_recommended.build_tfidf_vectorizer()

        self.assertIsNone(vectorizer.get_params()["stop_words"])
        recommendation_recommended.get_spanish_stopwords.cache_clear()

    @patch("applications.recommendation_system.recommended.stopwords.words", return_value=["de", "la"])
    def test_build_tfidf_vectorizer_uses_list_stopwords_compatible_with_sklearn(self, _mock_words):
        """Las stopwords cacheadas deben entregarse como lista, no tuple, para scikit-learn actual."""
        recommendation_recommended.get_spanish_stopwords.cache_clear()

        vectorizer = recommendation_recommended.build_tfidf_vectorizer()

        self.assertEqual(vectorizer.get_params()["stop_words"], ["de", "la"])
        recommendation_recommended.get_spanish_stopwords.cache_clear()
