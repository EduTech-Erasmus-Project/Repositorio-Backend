"""Pruebas del flujo completo de evaluación estudiantil sobre OAs.

Esta suite valida el recorrido real del estudiante:
- autenticarse
- evaluar un OA ya cargado con metadata real
- consultar resultados
- proteger reglas como unicidad por estudiante y rollback ante fallos internos

también cubre casos delicados del payload, como mantener el mapeo de respuestas
por `question_id` aunque el orden cambie entre create, update o recarga.
"""

import io
import shutil
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from applications.education_level.models import EducationLevel
from applications.evaluation_collaborating_expert.models import EvaluationConcept
from applications.evaluation_student.models import (
    EvaluationGuidelineQualification,
    EvaluationPrincipleQualification,
    EvaluationQuestionQualification,
    Guideline,
    Principle,
    Question,
    StudentEvaluation,
)
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import Student, Teacher
from test.helpers.oa_real_zip_utils import (
    build_metadata_payload_from_upload,
    build_real_zip_upload_file,
)
from test.helpers.temp_media_root import build_test_media_root


class StudentEvaluationFlowTests(TestCase):
    """Cubre el flujo end-to-end del estudiante evaluando un OA real."""

    def setUp(self):
        """Prepara usuarios, OA real, metadata mínima y pregunta base.

        La fixture monta un escenario realista para el módulo:
        - un docente que publica el OA
        - un estudiante que lo evaluara
        - conceptos mínimos requeridos para metadata
        - un OA creado desde ZIP real de prueba
        - correo parcheado para evitar side effects externos
        """
        self.client = APIClient()
        self.user_model = get_user_model()
        self.media_root = build_test_media_root("test-media-student-eval-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()
        self._start_mail_patches()

        self.teacher_user = self._create_teacher_user()
        self.student_user = self._create_student_user()
        self._question_sequence = 0
        self._create_minimum_metadata_evaluation_concepts()
        self.learning_object = self._create_learning_object_from_real_zip()
        self.question = self._create_student_question()

    def tearDown(self):
        """Libera MEDIA_ROOT temporal y borra archivos generados por la suite."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _start_mail_patches(self):
        """Desactiva envíos reales de correo disparados por el flujo del OA."""
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
            "avatar-student-eval.png",
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
        """Crea el docente que pública el OA usado en las evaluaciones."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-student-eval@example.com",
            first_name="Teacher",
            last_name="StudentEval",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_student_user(self):
        """Crea el estudiante principal que ejecuta la evaluación."""
        student = Student.objects.create(
            birthday=date(2001, 1, 1),
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="student-eval@example.com",
            first_name="Student",
            last_name="Evaluator",
            password="StrongPass123",
        )
        user.student = student
        user.save()
        return user

    def _create_minimum_metadata_evaluation_concepts(self):
        """Crea el concepto mínimo requerido por el flujo de metadata."""
        EvaluationConcept.objects.create(concept="Concepto metadata base")

    def _create_learning_object_from_real_zip(self):
        """Publica un OA real desde fixture para probar el flujo estudiantil."""
        self._login_and_set_bearer("teacher-student-eval@example.com", "StrongPass123")

        upload_response = self.client.post(
            "/api/v1/learning-object-file/",
            {"file": self._build_real_zip_from_fixture()},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.data)

        education_level = EducationLevel.objects.create(
            name_es="Nivel Eval Student",
            name_en="Student Eval Level",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Eval Student",
            description_es="Desc",
            name_en="Student Eval Area",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Eval Student",
            name_en="Student Eval License",
            value="STUDENT-EVAL-LICENSE",
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

    def _create_student_question(self, principle_name=None, guideline_name=None, question_text=None):
        """Crea una pregunta estudiantil completa con su principio y guideline."""
        self._question_sequence += 1
        seq = self._question_sequence
        principle = Principle.objects.create(
            principle=principle_name or f"Principio Student Eval {seq}"
        )
        guideline = Guideline.objects.create(
            guideline=guideline_name or f"Guideline Student Eval {seq}",
            principle=principle,
        )
        return Question.objects.create(
            question=question_text or f"Pregunta Student Eval {seq}",
            description="Descripcion",
            metadata="metadata",
            interpreter_st_yes="yes",
            interpreter_st_no="no",
            interpreter_st_partially="partial",
            interpreter_st_not_apply="na",
            value_st_importance=1.0,
            relevance="high",
            weight=1.0,
            guideline=guideline,
        )

    def _login_and_set_bearer(self, email, password):
        """Autentica el cliente compartido y fija el bearer token correspondiente."""
        response = self.client.post(
            "/api/v1/login/",
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def _build_student_evaluation_payload(self):
        """Construye un payload valido de evaluación estudiantil sobre el OA base."""
        return {
            "learning_object": self.learning_object.id,
            "observation": "Evaluacion por estudiante",
            "results": [
                {
                    "id": self.question.id,
                    "value": "Si",
                }
            ],
        }

    def _build_student_result_map(self):
        """Reconstruye un mapa `question_id -> qualification` desde la respuesta."""
        response = self.client.get(
            f"/api/v1/learning-objects/student/result-to-student/{self.learning_object.id}/"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)

        result_map = {}
        for principle in response.data[0]["evaluation_students"]:
            for guideline in principle["principle_gl"]:
                for question in guideline["guideline_evaluations"]:
                    result_map[question["question_id"]] = question["qualification"]
        return result_map

    def _build_student_result_order(self):
        """Extrae el orden en que la API devuelve las preguntas evaluadas."""
        response = self.client.get(
            f"/api/v1/learning-objects/student/result-to-student/{self.learning_object.id}/"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)

        result_order = []
        for principle in response.data[0]["evaluation_students"]:
            for guideline in principle["principle_gl"]:
                for question in guideline["guideline_evaluations"]:
                    result_order.append(question["question_id"])
        return result_order

    def test_student_can_create_and_consult_learning_object_evaluation(self):
        """Permite registrar una evaluación y consultar su resultado."""
        self._login_and_set_bearer("student-eval@example.com", "StrongPass123")

        create_response = self.client.post(
            "/api/v1/learning-objects/student-evaluation/",
            self._build_student_evaluation_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        self.assertEqual(StudentEvaluation.objects.count(), 1)
        self.assertEqual(EvaluationQuestionQualification.objects.count(), 1)

        result_response = self.client.get(
            f"/api/v1/learning-objects/student/result-to-student/{self.learning_object.id}/"
        )
        self.assertEqual(result_response.status_code, 200, result_response.data)
        self.assertEqual(len(result_response.data), 1)
        self.assertEqual(
            result_response.data[0]["learning_object"],
            self.learning_object.id,
        )

    def test_student_cannot_evaluate_same_learning_object_twice(self):
        """Evita evaluar dos veces el mismo OA por el mismo estudiante."""
        self._login_and_set_bearer("student-eval@example.com", "StrongPass123")
        payload = self._build_student_evaluation_payload()

        first_response = self.client.post(
            "/api/v1/learning-objects/student-evaluation/",
            payload,
            format="json",
        )
        self.assertEqual(first_response.status_code, 200, first_response.data)

        second_response = self.client.post(
            "/api/v1/learning-objects/student-evaluation/",
            payload,
            format="json",
        )
        self.assertEqual(second_response.status_code, 400, second_response.data)
        self.assertEqual(second_response.data["message"], "Este ya fue evaluado")

    def test_student_evaluation_create_rolls_back_if_nested_write_fails(self):
        """Si una escritura interna falla, no debe quedar evaluación parcial persistida."""
        self._login_and_set_bearer("student-eval@example.com", "StrongPass123")

        with patch(
            "applications.evaluation_student.views.EvaluationQuestionQualification.objects.create",
            side_effect=RuntimeError("fallo forzado en pregunta"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    "/api/v1/learning-objects/student-evaluation/",
                    self._build_student_evaluation_payload(),
                    format="json",
                )

        self.assertEqual(StudentEvaluation.objects.count(), 0)
        self.assertEqual(EvaluationQuestionQualification.objects.count(), 0)

    def test_student_evaluation_create_keeps_answers_mapped_by_question_id(self):
        """Create debe persistir cada respuesta en su pregunta correcta aunque cambie la guideline."""
        second_question = self._create_student_question(
            principle_name="Principio Student Eval 2",
            guideline_name="Guideline Student Eval 2",
            question_text="Pregunta Student Eval 2",
        )
        self._login_and_set_bearer("student-eval@example.com", "StrongPass123")

        response = self.client.post(
            "/api/v1/learning-objects/student-evaluation/",
            {
                "learning_object": self.learning_object.id,
                "observation": "Evaluacion con dos preguntas",
                "results": [
                    {"id": self.question.id, "value": "Si"},
                    {"id": second_question.id, "value": "No"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

        result_map = self._build_student_result_map()
        self.assertEqual(result_map[self.question.id], "Si")
        self.assertEqual(result_map[second_question.id], "No")

    def test_student_evaluation_update_keeps_answers_mapped_by_question_id(self):
        """Update no debe mezclar respuestas cuando el payload llega en orden distinto."""
        second_question = self._create_student_question(
            principle_name="Principio Student Eval 2 Update",
            guideline_name="Guideline Student Eval 2 Update",
            question_text="Pregunta Student Eval 2 Update",
        )
        self._login_and_set_bearer("student-eval@example.com", "StrongPass123")

        create_response = self.client.post(
            "/api/v1/learning-objects/student-evaluation/",
            {
                "learning_object": self.learning_object.id,
                "observation": "Evaluacion inicial",
                "results": [
                    {"id": self.question.id, "value": "Si"},
                    {"id": second_question.id, "value": "No"},
                ],
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.data)
        evaluation_id = create_response.data["id"]

        update_response = self.client.put(
            f"/api/v1/learning-objects/student-evaluation/{evaluation_id}/",
            {
                "learning_object": self.learning_object.id,
                "observation": "Evaluacion actualizada",
                "results": [
                    {"id": second_question.id, "value": "No aplica"},
                    {"id": self.question.id, "value": "Parcialmente"},
                ],
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)

        result_map = self._build_student_result_map()
        self.assertEqual(result_map[self.question.id], "Parcialmente")
        self.assertEqual(result_map[second_question.id], "No aplica")

    def test_student_result_to_update_returns_questions_in_catalog_order(self):
        """La recarga para editar debe respetar el orden canónico de preguntas."""
        first_question = self._create_student_question(
            principle_name="Principio Student Eval Orden 1",
            guideline_name="Guideline Student Eval Orden 1",
            question_text="Pregunta Student Eval Orden 1",
        )
        second_question = self._create_student_question(
            principle_name="Principio Student Eval Orden 2",
            guideline_name="Guideline Student Eval Orden 2",
            question_text="Pregunta Student Eval Orden 2",
        )

        evaluation = StudentEvaluation.objects.create(
            learning_object=self.learning_object,
            observation="Orden de recarga",
            rating=0.0,
            student=self.student_user,
        )
        principle_two = EvaluationPrincipleQualification.objects.create(
            evaluation_principle=second_question.guideline.principle,
            evaluation_student=evaluation,
            average_principle=0.0,
        )
        principle_one = EvaluationPrincipleQualification.objects.create(
            evaluation_principle=first_question.guideline.principle,
            evaluation_student=evaluation,
            average_principle=0.0,
        )
        guideline_two = EvaluationGuidelineQualification.objects.create(
            guideline_pr=second_question.guideline,
            principle_gl=principle_two,
            average_guideline=0.0,
        )
        guideline_one = EvaluationGuidelineQualification.objects.create(
            guideline_pr=first_question.guideline,
            principle_gl=principle_one,
            average_guideline=0.0,
        )
        EvaluationQuestionQualification.objects.create(
            guideline_evaluations=guideline_two,
            evaluation_question=second_question,
            qualification=1.0,
        )
        EvaluationQuestionQualification.objects.create(
            guideline_evaluations=guideline_one,
            evaluation_question=first_question,
            qualification=1.0,
        )

        self._login_and_set_bearer("student-eval@example.com", "StrongPass123")

        result_order = self._build_student_result_order()
        self.assertEqual(result_order, [first_question.id, second_question.id])
