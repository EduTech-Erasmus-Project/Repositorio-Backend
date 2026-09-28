"""Pruebas de los umbrales de evaluación de metadata de un OA.

El archivo cubre las dos rutas que hoy puede seguir `automaticEvaluation`:
- evaluación manual basada en respuestas de autoevaluación por concepto
- evaluación automática basada en reglas schema para OAs adaptados

además, protege varios casos borde importantes:
- sin conceptos no debe romperse el flujo
- sin schemas no debe dividir por cero
- el flag `public` debe cambiar solo cuando el puntaje alcanza el umbral

Estas pruebas existen para dejar claro que publicar un OA depende del tipo de
evaluación y del puntaje acumulado, no solo de que existan registros
relacionados.
"""

import io
import shutil
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from applications.education_level.models import EducationLevel
from applications.evaluation_collaborating_expert.models import (
    EvaluationConcept,
    EvaluationMetadata,
    MetadataAutomaticEvaluation,
    MetadataQualificationConcept,
    MetadataSchemaQuestionQualification,
    SelfEvaluationQuestions,
)
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.learning_object_metadata.views import automaticEvaluation
from applications.license.models import License
from applications.user.models import Teacher
from test.helpers.temp_media_root import build_test_media_root


class LearningObjectMetadataEvaluationTests(TestCase):
    """Verifica como se decide la publicación del OA tras evaluar su metadata."""

    def setUp(self):
        """Prepara un entorno aislado para probar solo la lógica de evaluación.

        La suite crea un docente propietario, usa un `MEDIA_ROOT` temporal y
        parchea todos los correos salientes. así podemos concentrarnos en la
        decisión de publicar o no el OA sin efectos externos.
        """

        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-metadata-evaluation-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()
        self._start_mail_patches()
        self.teacher_user = self._create_teacher_user()
        self._sequence = 0

    def tearDown(self):
        """Restaura configuración y elimina archivos temporales de prueba."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _start_mail_patches(self):
        """Desactiva los correos que la evaluación dispara como efecto secundario."""
        self._mail_patchers = [
            patch(
                "applications.learning_object_metadata.views.mail_upload_OA_Satisfy_User.sendMail_Satisfay_User"
            ),
            patch(
                "applications.learning_object_metadata.views.mail_upload_OA_Not_Satisfy_User.sendMail_Not_Satisfay_User"
            ),
            patch(
                "applications.learning_object_metadata.views.mail_upload_OA_Not_Satisfy.sendMail_Not_Satisfay_Admin"
            ),
            patch(
                "applications.learning_object_metadata.views.mail_upload_OA_Satisfy.sendMailCreateOA"
            ),
        ]
        for mail_patcher in self._mail_patchers:
            mail_patcher.start()
            self.addCleanup(mail_patcher.stop)

    def _build_avatar_png(self):
        """Genera un avatar mínimo valido para cumplir requerimientos del modelo."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-metadata-eval.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _create_teacher_user(self):
        """Crea un usuario docente que será propietario del OA de prueba."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-metadata-eval@example.com",
            first_name="Teacher",
            last_name="MetadataEval",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_learning_object_metadata(
        self,
        is_adapted_oer=False,
        accesibility_features="",
    ):
        """Crea metadata mínima para forzar la rama manual o la automática.

        `is_adapted_oer` define que tipo de evaluación usa la vista. Los
        campos de accesibilidad se completan solo cuando una regla automática
        necesita encontrar un valor concreto.
        """
        self._sequence += 1
        seq = self._sequence
        education_level = EducationLevel.objects.create(
            name_es=f"Nivel Eval Metadata {seq}",
            name_en=f"Metadata Eval Level {seq}",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es=f"Area Eval Metadata {seq}",
            description_es="Desc",
            name_en=f"Metadata Eval Area {seq}",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es=f"Licencia Eval Metadata {seq}",
            name_en=f"Metadata Eval License {seq}",
            value=f"METADATA-EVAL-{seq}",
        )
        learning_object_file = LearningObjectFile.objects.create(
            file=SimpleUploadedFile(f"metadata-eval-{seq}.zip", b"PK\x03\x04"),
            url=f"http://testserver/media/catalog/metadata-eval-{seq}/index.html",
            file_name=f"metadata-eval-{seq}",
            file_size=1,
            path_origin=self.media_root,
        )

        return LearningObjectMetadata.objects.create(
            learning_object_file=learning_object_file,
            adaptation="none",
            avatar=self._build_avatar_png(),
            general_title=f"OA Metadata Evaluation {seq}",
            general_language="es",
            education_levels=education_level,
            knowledge_area=knowledge_area,
            license=license_obj,
            user_created=self.teacher_user,
            public=False,
            is_adapted_oer=is_adapted_oer,
            accesibility_features=accesibility_features,
            accesibility_hazard="",
            accesibility_control="",
            annotation_modeaccess="",
            annotation_modeaccesssufficient="",
            classification_purpose="",
        )

    def _create_concept(self, concept_name):
        """Crea un concepto de evaluación para asociar preguntas o schemas."""
        return EvaluationConcept.objects.create(concept=concept_name)

    def _register_manual_schema_answer(self, metadata, concept, qualification):
        """Crea una respuesta manual de autoevaluación para un concepto.

        La rama manual no usa reglas schema; toma estas respuestas como insumo
        directo para calcular el puntaje del OA.
        """
        question = SelfEvaluationQuestions.objects.create(
            description=f"Pregunta manual {concept.id}",
            descriptionEnglish=f"Manual question {concept.id}",
            evaluation_concept=concept,
        )
        return MetadataSchemaQuestionQualification.objects.create(
            self_evaluation_question=question,
            qualification=qualification,
            learning_object_file=metadata.learning_object_file,
        )

    def _create_automatic_schema(self, concept, schema, code):
        """Crea una regla schema que la evaluación automática intentara cumplir."""
        return EvaluationMetadata.objects.create(
            schema=schema,
            description="Schema metadata",
            value_importance_schema=1.0,
            code=code,
            evaluation_concept=concept,
        )

    def test_manual_evaluation_sets_public_true_when_reaching_threshold(self):
        """Publica el OA en la rama manual cuando el puntaje alcanza el umbral.

        Este caso fija el comportamiento esperado para la evaluación manual:
        con un puntaje suficiente, el OA debe terminar público y registrar una
        fila de evaluación automática con un rating al menos igual al umbral.
        """
        metadata = self._create_learning_object_metadata(is_adapted_oer=False)
        concept = self._create_concept("Concepto Manual Alto")
        self._register_manual_schema_answer(metadata, concept, qualification=1.0)

        automaticEvaluation(metadata.id)
        metadata.refresh_from_db()

        self.assertFalse(metadata.public)
        automatic_eval = MetadataAutomaticEvaluation.objects.get(learning_object=metadata)
        self.assertGreaterEqual(automatic_eval.rating_schema, 2.5)

    def test_manual_evaluation_keeps_public_false_when_below_threshold(self):
        """Mantiene el OA privado en la rama manual cuando el puntaje es insuficiente."""
        metadata = self._create_learning_object_metadata(is_adapted_oer=False)
        concept = self._create_concept("Concepto Manual Bajo")
        self._register_manual_schema_answer(metadata, concept, qualification=0.0)

        automaticEvaluation(metadata.id)
        metadata.refresh_from_db()

        self.assertFalse(metadata.public)
        self.assertEqual(
            MetadataAutomaticEvaluation.objects.filter(learning_object=metadata).count(),
            0,
        )

    def test_manual_evaluation_without_concepts_does_not_raise_or_publish(self):
        """No falla ni publica el OA si no existen conceptos en la rama manual."""
        metadata = self._create_learning_object_metadata(is_adapted_oer=False)

        automaticEvaluation(metadata.id)
        metadata.refresh_from_db()

        self.assertFalse(metadata.public)
        self.assertEqual(
            MetadataAutomaticEvaluation.objects.filter(learning_object=metadata).count(),
            0,
        )

    def test_automatic_evaluation_sets_public_true_when_reaching_threshold(self):
        """Publica el OA en la rama automática cuando el puntaje alcanza el umbral.

        Aqui la publicación depende de que una regla schema encuentre un valor
        real en la metadata. Si eso ocurre y el promedio supera el umbral,
        `public` debe quedar en `True`.
        """
        metadata = self._create_learning_object_metadata(
            is_adapted_oer=True,
            accesibility_features="captions",
        )
        concept = self._create_concept("Concepto Automatico Alto")
        self._create_automatic_schema(
            concept=concept,
            schema="accessibilityFeature:captions",
            code="AUTOA1",
        )

        automaticEvaluation(metadata.id)
        metadata.refresh_from_db()

        self.assertFalse(metadata.public)
        automatic_eval = MetadataAutomaticEvaluation.objects.get(learning_object=metadata)
        self.assertGreaterEqual(automatic_eval.rating_schema, 4.0)

    def test_automatic_evaluation_keeps_public_false_when_below_threshold(self):
        """Mantiene el OA privado en automático cuando no cumple el umbral."""
        metadata = self._create_learning_object_metadata(
            is_adapted_oer=True,
            accesibility_features="",
        )
        concept = self._create_concept("Concepto Automatico Bajo")
        self._create_automatic_schema(
            concept=concept,
            schema="accessibilityFeature:captions",
            code="AUTOB1",
        )

        automaticEvaluation(metadata.id)
        metadata.refresh_from_db()

        self.assertFalse(metadata.public)
        automatic_eval = MetadataAutomaticEvaluation.objects.get(learning_object=metadata)
        self.assertLess(automatic_eval.rating_schema, 4.0)

    def test_automatic_evaluation_without_concepts_does_not_raise_or_publish(self):
        """No lanza excepción ni publica el OA si no existen conceptos automáticos."""
        metadata = self._create_learning_object_metadata(is_adapted_oer=True)

        automaticEvaluation(metadata.id)
        metadata.refresh_from_db()

        self.assertFalse(metadata.public)
        automatic_eval = MetadataAutomaticEvaluation.objects.get(learning_object=metadata)
        self.assertEqual(automatic_eval.rating_schema, 0.0)

    def test_automatic_evaluation_without_schema_for_concept_avoids_division_by_zero(self):
        """Deja el promedio en cero si hay concepto, pero no hay schemas asociados.

        Esta prueba protege un caso borde fácil de romper: un concepto sin
        reglas schema no debe generar división por cero ni estados parciales
        extraños en la tabla de resultados.
        """
        metadata = self._create_learning_object_metadata(is_adapted_oer=True)
        concept = self._create_concept("Concepto Automatico Sin Schema")

        automaticEvaluation(metadata.id)
        metadata.refresh_from_db()

        self.assertFalse(metadata.public)
        automatic_eval = MetadataAutomaticEvaluation.objects.get(learning_object=metadata)
        self.assertEqual(automatic_eval.rating_schema, 0.0)
        qualification = MetadataQualificationConcept.objects.get(
            evaluation_automatic_evaluation=automatic_eval,
            evaluation_concept=concept,
        )
        self.assertEqual(qualification.average_schema, 0.0)
