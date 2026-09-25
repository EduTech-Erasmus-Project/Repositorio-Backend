"""Pruebas del flujo completo de evaluación experta sobre OAs.

Esta suite cubre el recorrido real del experto colaborador:
- preparar un OA desde un ZIP de fixture
- registrar la evaluación del OA
- consultar, actualizar y eliminar esa evaluación
- validar reglas de negocio como unicidad por experto y rollback ante fallos

Es una suite más cercana a integración que a CRUD simple, porque mezcla login,
archivos, metadata, preguntas expertas y persistencia de calificaciones.
"""

import io
import shutil
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.evaluation_collaborating_expert.models import (
    EvaluationCollaboratingExpert,
    EvaluationConcept,
    EvaluationConceptQualification,
    EvaluationQuestion,
    EvaluationQuestionsQualification,
)
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import CollaboratingExpert, Student, Teacher
from test.helpers.oa_real_zip_utils import (
    build_metadata_payload_from_upload,
    build_real_zip_upload_file,
)
from test.helpers.temp_media_root import build_test_media_root


class ExpertEvaluationFlowTests(TransactionTestCase):
    """Cubre el flujo end-to-end del experto colaborador sobre un OA real."""

    def setUp(self):
        """Prepara usuarios, preguntas, OA base y media temporal.

        La fixture arma un escenario completo para que las pruebas operen sobre
        un OA real de prueba y no sobre mocks excesivos:
        - usuarios teacher, expert y student
        - preguntas expertas ya creadas
        - upload y metadata de un OA desde ZIP real
        - correo parcheado para evitar side effects externos
        """
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-expert-eval-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()
        self._start_mail_patches()

        self.teacher_user = self._create_teacher_user()
        self.expert_user = self._create_expert_user()
        self.student_user = self._create_student_user()
        self.questions = self._create_expert_questions()
        self.learning_object = self._create_learning_object_from_real_zip()

    def tearDown(self):
        """Limpia MEDIA_ROOT temporal y archivos generados por la suite."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _start_mail_patches(self):
        """Desactiva envíos reales de correo durante el flujo del OA."""
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
        """Genera un PNG mínimo para el payload multipart de metadata."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-expert-eval.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _build_real_zip_from_fixture(self):
        """Carga el ZIP real de fixture o falla explicando el problema."""
        try:
            return build_real_zip_upload_file()
        except FileNotFoundError as exc:
            self.fail(str(exc))

    def _create_teacher_user(self):
        """Crea el docente que publica el OA usado luego en la evaluación."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-expert-eval@example.com",
            first_name="Teacher",
            last_name="ExpertEval",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_expert_user(self):
        """Crea el experto principal que ejecuta la mayoría de pruebas."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Alto",
            web="https://expert.local",
            academic_profile="QA profile",
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="expert-eval@example.com",
            first_name="Expert",
            last_name="Evaluator",
            password="StrongPass123",
        )
        user.collaboratingExpert = expert
        user.save()
        return user

    def _create_second_expert_user(self):
        """Crea un segundo experto para probar restricciones de propiedad."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Medio",
            web="https://expert-2.local",
            academic_profile="QA profile 2",
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="expert-eval-2@example.com",
            first_name="Expert",
            last_name="EvaluatorTwo",
            password="StrongPass123",
        )
        user.collaboratingExpert = expert
        user.save()
        return user

    def _create_student_user(self):
        """Crea un usuario no experto para comprobar permisos denegados."""
        student = Student.objects.create(
            birthday=date(2002, 1, 1),
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-not-expert@example.com",
            first_name="Student",
            last_name="NotExpert",
            password="StrongPass123",
        )
        user.student = student
        user.save()
        return user

    def _create_learning_object_from_real_zip(self):
        """Publica un OA real desde fixture para usarlo en las evaluaciones.

        El helper autentica al docente, sube un ZIP real, crea metadata
        asociada y devuelve la instancia `LearningObjectMetadata` resultante.
        así las pruebas ejercitan el flujo del experto sobre un OA cercano a un
        caso real y no sobre datos creados a mano de forma artificial.
        """
        self._login_and_set_bearer("teacher-expert-eval@example.com", "StrongPass123")

        upload_response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": self._build_real_zip_from_fixture()},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.data)

        education_level = EducationLevel.objects.create(
            name_es="Nivel Eval Expert",
            name_en="Expert Eval Level",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Eval Expert",
            description_es="Desc",
            name_en="Expert Eval Area",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Eval Expert",
            name_en="Expert Eval License",
            value="EXPERT-EVAL-LICENSE",
        )
        metadata_payload = build_metadata_payload_from_upload(
            upload_response.data,
            education_level_id=education_level.id,
            knowledge_area_id=knowledge_area.id,
            license_id=license_obj.id,
            avatar_file=self._build_avatar_png(),
        )
        metadata_create_response = self.client.post(
            "/api/v1/learning-object-metadata/",
            metadata_payload,
            format="multipart",
        )
        self.assertEqual(
            metadata_create_response.status_code,
            201,
            metadata_create_response.data,
        )
        metadata = LearningObjectMetadata.objects.get(id=metadata_create_response.data["id"])
        self.assertEqual(metadata.general_title, metadata_payload["general_title"])
        return metadata

    def _create_expert_questions(self):
        """Crea los conceptos y preguntas mínimos para una evaluación completa."""
        concepts = [
            EvaluationConcept.objects.create(concept="Concepto Expert Eval 1"),
            EvaluationConcept.objects.create(concept="Concepto Expert Eval 2"),
            EvaluationConcept.objects.create(concept="Concepto Expert Eval 3"),
            EvaluationConcept.objects.create(concept="Concepto Expert Eval 4"),
        ]

        questions = []
        for idx, concept in enumerate(concepts, start=1):
            question = EvaluationQuestion.objects.create(
                question=f"Pregunta Expert Eval {idx}",
                description="Descripcion",
                schema=f"schema:{idx}",
                interpreter_yes="yes",
                interpreter_no="no",
                interpreter_partially="partial",
                interpreter_not_apply="na",
                value_importance=1.0,
                relevance="high",
                weight=1.0,
                code=f"QAE{idx}",
                evaluation_concept=concept,
            )
            questions.append(question)
        return questions

    def _login_and_set_bearer(self, email, password):
        """Autentica el cliente compartido y fija el bearer token correspondiente."""
        response = self.client.post(
            "/api/v1/login/",
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def _build_expert_evaluation_payload(self):
        """Construye un payload valido de evaluación experta sobre el OA base."""
        return {
            "learning_object": self.learning_object.id,
            "observation": "Evaluacion por experto",
            "results": [
                {"id": self.questions[0].id, "value": "Si"},
                {"id": self.questions[1].id, "value": "No"},
                {"id": self.questions[2].id, "value": "Parcialmente"},
                {"id": self.questions[3].id, "value": "Si"},
            ],
        }

    def test_expert_can_create_and_consult_learning_object_evaluation(self):
        """Verifica alta completa y consulta posterior de la evaluación creada.

        Ademas del 200 del endpoint, esta prueba confirma que se crean los
        registros relacionados esperados: evaluación principal, promedios por
        concepto y calificaciones por pregunta.
        """
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")

        create_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)

        self.assertEqual(EvaluationCollaboratingExpert.objects.count(), 1)
        self.assertEqual(EvaluationConceptQualification.objects.count(), 4)
        self.assertEqual(EvaluationQuestionsQualification.objects.count(), 4)
        created_eval = EvaluationCollaboratingExpert.objects.first()
        self.assertTrue(created_eval.is_priority)

        result_response = self.client.get(
            f"/api/v1/learning-objects/evaluations-result-to-expert/{self.learning_object.id}/"
        )
        self.assertEqual(result_response.status_code, 200, result_response.data)
        self.assertEqual(len(result_response.data), 1)
        self.assertEqual(
            result_response.data[0]["learning_object"],
            self.learning_object.id,
        )

    def test_expert_cannot_evaluate_same_learning_object_twice(self):
        """Impide doble evaluación del mismo OA por el mismo experto."""
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        payload = self._build_expert_evaluation_payload()

        first_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            payload,
            format="json",
        )
        self.assertEqual(first_response.status_code, 200, first_response.data)

        second_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            payload,
            format="json",
        )
        self.assertEqual(second_response.status_code, 400, second_response.data)
        self.assertEqual(
            second_response.data["message"],
            "Learning Object is already evaluated by this expert",
        )

    def test_non_expert_user_cannot_create_expert_evaluation(self):
        """Bloquea que un usuario sin rol experto registre evaluaciones expertas."""
        self._login_and_set_bearer("student-not-expert@example.com", "StrongPass123")

        response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_expert_evaluation_with_all_not_apply_returns_zero_rating(self):
        """Valida el caso borde donde todas las respuestas son `No aplica`.

        El flujo no debe romperse ni producir ratings inconsistentes; la
        evaluación debe guardarse con promedio cero en cada concepto.
        """
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        payload = {
            "learning_object": self.learning_object.id,
            "observation": "Evaluacion sin respuestas aplicables",
            "results": [
                {"id": question.id, "value": "No aplica"}
                for question in self.questions
            ],
        }

        response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

        evaluation = EvaluationCollaboratingExpert.objects.get(id=response.data["id"])
        self.assertEqual(float(evaluation.rating), 0.0)
        self.assertEqual(
            EvaluationConceptQualification.objects.filter(
                evaluation_collaborating_expert=evaluation,
                average=0.0,
            ).count(),
            4,
        )

    def test_expert_can_list_and_retrieve_own_evaluation(self):
        """Valida list/retrieve del ViewSet para el experto autenticado."""
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        create_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        evaluation_id = create_response.data["id"]

        list_response = self.client.get("/api/v1/learning-objects/register-evaluation-expert/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], evaluation_id)

        retrieve_response = self.client.get(
            f"/api/v1/learning-objects/register-evaluation-expert/{evaluation_id}/"
        )
        self.assertEqual(retrieve_response.status_code, 200, retrieve_response.data)
        self.assertEqual(retrieve_response.data["id"], evaluation_id)

    def test_expert_can_update_own_evaluation(self):
        """Valida update de evaluación propia y persistencia de observación."""
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        create_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        evaluation_id = create_response.data["id"]
        previous_rating = create_response.data["rating"]

        update_payload = {
            "learning_object": self.learning_object.id,
            "observation": "Evaluacion actualizada por experto",
            "results": [
                {"id": self.questions[0].id, "value": "No"},
                {"id": self.questions[1].id, "value": "No"},
                {"id": self.questions[2].id, "value": "Parcialmente"},
                {"id": self.questions[3].id, "value": "Si"},
            ],
        }
        update_response = self.client.put(
            f"/api/v1/learning-objects/register-evaluation-expert/{evaluation_id}/",
            update_payload,
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)

        updated_eval = EvaluationCollaboratingExpert.objects.get(id=evaluation_id)
        self.assertEqual(updated_eval.observation, "Evaluacion actualizada por experto")
        self.assertNotEqual(float(previous_rating), float(updated_eval.rating))

    def test_expert_update_rolls_back_if_average_update_fails(self):
        """Si falla el recalculo de promedios, no debe persistirse una actualización parcial."""
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        create_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        evaluation_id = create_response.data["id"]
        created_eval = EvaluationCollaboratingExpert.objects.get(id=evaluation_id)
        previous_observation = created_eval.observation
        previous_rating = float(created_eval.rating)
        previous_qualifications = list(
            EvaluationQuestionsQualification.objects.filter(
                concept_evaluations__evaluation_collaborating_expert_id=evaluation_id
            )
            .order_by("evaluation_question_id")
            .values_list("evaluation_question_id", "qualification")
        )

        update_payload = {
            "learning_object": self.learning_object.id,
            "observation": "Debe hacer rollback",
            "results": [
                {"id": self.questions[0].id, "value": "No"},
                {"id": self.questions[1].id, "value": "Si"},
                {"id": self.questions[2].id, "value": "No aplica"},
                {"id": self.questions[3].id, "value": "Parcialmente"},
            ],
        }

        with patch(
            "applications.evaluation_collaborating_expert.views.updateAverage",
            side_effect=RuntimeError("average failed"),
        ):
            self.client.raise_request_exception = False
            update_response = self.client.put(
                f"/api/v1/learning-objects/register-evaluation-expert/{evaluation_id}/",
                update_payload,
                format="json",
            )
            self.client.raise_request_exception = True

        self.assertEqual(update_response.status_code, 500)

        created_eval.refresh_from_db()
        current_qualifications = list(
            EvaluationQuestionsQualification.objects.filter(
                concept_evaluations__evaluation_collaborating_expert_id=evaluation_id
            )
            .order_by("evaluation_question_id")
            .values_list("evaluation_question_id", "qualification")
        )
        self.assertEqual(created_eval.observation, previous_observation)
        self.assertEqual(float(created_eval.rating), previous_rating)
        self.assertEqual(current_qualifications, previous_qualifications)

    def test_expert_cannot_update_other_expert_evaluation(self):
        """Bloquea update de evaluaciones que pertenecen a otro experto."""
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        create_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        evaluation_id = create_response.data["id"]

        self._create_second_expert_user()
        self._login_and_set_bearer("expert-eval-2@example.com", "StrongPass123")
        response = self.client.put(
            f"/api/v1/learning-objects/register-evaluation-expert/{evaluation_id}/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_expert_can_delete_own_evaluation_and_related_records(self):
        """Elimina evaluación propia y sus calificaciones asociadas."""
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        create_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        evaluation_id = create_response.data["id"]

        self.assertTrue(
            EvaluationConceptQualification.objects.filter(
                evaluation_collaborating_expert_id=evaluation_id
            ).exists()
        )
        self.assertTrue(
            EvaluationQuestionsQualification.objects.filter(
                concept_evaluations__evaluation_collaborating_expert_id=evaluation_id
            ).exists()
        )

        delete_response = self.client.delete(
            f"/api/v1/learning-objects/register-evaluation-expert/{evaluation_id}/"
        )
        self.assertEqual(delete_response.status_code, 200, delete_response.data)
        self.assertFalse(EvaluationCollaboratingExpert.objects.filter(id=evaluation_id).exists())
        self.assertFalse(
            EvaluationConceptQualification.objects.filter(
                evaluation_collaborating_expert_id=evaluation_id
            ).exists()
        )
        self.assertFalse(
            EvaluationQuestionsQualification.objects.filter(
                concept_evaluations__evaluation_collaborating_expert_id=evaluation_id
            ).exists()
        )

    def test_expert_delete_rolls_back_if_related_delete_fails(self):
        """Si falla un borrado relacionado, la evaluación y sus detalles deben recuperarse."""
        self._login_and_set_bearer("expert-eval@example.com", "StrongPass123")
        create_response = self.client.post(
            "/api/v1/learning-objects/register-evaluation-expert/",
            self._build_expert_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        evaluation_id = create_response.data["id"]

        with patch(
            "applications.evaluation_collaborating_expert.views.EvaluationConceptQualification.delete",
            side_effect=RuntimeError("delete failed"),
        ):
            self.client.raise_request_exception = False
            delete_response = self.client.delete(
                f"/api/v1/learning-objects/register-evaluation-expert/{evaluation_id}/"
            )
            self.client.raise_request_exception = True

        self.assertEqual(delete_response.status_code, 500)

        self.assertTrue(EvaluationCollaboratingExpert.objects.filter(id=evaluation_id).exists())
        self.assertTrue(
            EvaluationConceptQualification.objects.filter(
                evaluation_collaborating_expert_id=evaluation_id
            ).exists()
        )
        self.assertTrue(
            EvaluationQuestionsQualification.objects.filter(
                concept_evaluations__evaluation_collaborating_expert_id=evaluation_id
            ).exists()
        )
