"""Pruebas administrativas del módulo `evaluation_student`.

Esta suite se concentra en el mantenimiento del catálogo que usa la evaluación
estudiantil:
- principios
- guidelines
- preguntas asociadas

Su objetivo es asegurar permisos, validaciones y CRUD sobre los recursos que
después consume el flujo real de evaluación del estudiante.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.evaluation_student.models import Guideline, Principle, Question
from applications.user.models import Administrator, Teacher


class AdminCrudPrinciplesGuidelinesQuestionsTests(TestCase):
    """Cubre el mantenimiento administrativo de principios, guidelines y preguntas."""

    def setUp(self):
        """Prepara clientes autenticados con tres perfiles de permisos.

        Se crean:
        - un administrador activo
        - un superusuario
        - un docente sin privilegios administrativos

        Esto permite comprobar acceso permitido y denegado sin repetir login en
        cada caso de prueba.
        """
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.admin_client = self._build_authenticated_client(self._create_admin_user())
        self.superuser_client = self._build_authenticated_client(self._create_superuser_user())
        self.teacher_client = self._build_authenticated_client(self._create_teacher_user())

    def _next_email(self, prefix):
        """Genera correos únicos para evitar colisiones entre pruebas."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _build_authenticated_client(self, user):
        """Autentica vía JWT y retorna un cliente listo para endpoints protegidos."""
        client = APIClient()
        login_response = client.post(
            "/api/v1/login/",
            {"email": user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        return client

    def _create_admin_user(self):
        """Crea el administrador usado para operaciones permitidas del CRUD."""
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin CRUD student",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin"),
            first_name="Admin",
            last_name="StudentCrud",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_superuser_user(self):
        """Crea un superusuario para comparar permisos equivalentes a admin."""
        return self.user_model.objects.create_superuser(
            email=self._next_email("superuser"),
            first_name="Super",
            last_name="StudentCrud",
            password=self.password,
        )

    def _create_teacher_user(self):
        """Crea un docente para comprobar denegación en el CRUD admin."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher"),
            first_name="Teacher",
            last_name="StudentCrud",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def _student_question_payload(self, guideline_id, suffix="A"):
        """Arma un payload valido para crear preguntas del catálogo estudiantil.

        El helper concentra los campos obligatorios del serializer y hace mas
        fácil leer en cada prueba que lo importante es el permiso o la
        validación, no el armado repetitivo del payload.
        """
        return {
            "question": f"Pregunta estudiante {suffix}",
            "description": "Descripcion",
            "metadata": "metadata",
            "interpreter_st_yes": "si",
            "interpreter_st_no": "no",
            "interpreter_st_partially": "parcial",
            "interpreter_st_not_apply": "na",
            "value_st_importance": 1.0,
            "relevance": "high",
            "weight": 1.0,
            "guideline": guideline_id,
        }

    def test_principle_create_requires_admin_permissions(self):
        """Permite crear principios solo a admin/superuser."""
        teacher_response = self.teacher_client.post(
            "/api/v1/learning-objects/student-register-principles/",
            {"principle": "Principio Prohibido"},
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/learning-objects/student-register-principles/",
            {"principle": "Principio Admin"},
            format="json",
        )
        self.assertEqual(admin_response.status_code, 201, admin_response.data)

        super_response = self.superuser_client.post(
            "/api/v1/learning-objects/student-register-principles/",
            {"principle": "Principio Super"},
            format="json",
        )
        self.assertEqual(super_response.status_code, 201, super_response.data)

    def test_principle_create_validates_required_and_unique(self):
        """Valida requerido y unicidad al crear principios."""
        empty = self.admin_client.post(
            "/api/v1/learning-objects/student-register-principles/",
            {},
            format="json",
        )
        self.assertEqual(empty.status_code, 400)
        self.assertIn("principle", empty.data)

        created = self.admin_client.post(
            "/api/v1/learning-objects/student-register-principles/",
            {"principle": "Principio Unico"},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)

        duplicate = self.admin_client.post(
            "/api/v1/learning-objects/student-register-principles/",
            {"principle": "Principio Unico"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("principle", duplicate.data)

    def test_principle_crud_update_and_delete_as_admin(self):
        """Actualiza y elimina un principio existente con permisos de admin."""
        principle_bd = Principle.objects.create(principle="Principio Original")

        payload = {
            "id": principle_bd.id,
            "principle": "Principio Actualizado",
        }

        update_response = self.admin_client.put(
            f"/api/v1/learning-objects/student-register-principles/{principle_bd.id}/",
            payload,
            format="json",
        )

        self.assertEqual(update_response.status_code, 200)
        
        principle_bd.refresh_from_db()

        self.assertEqual(principle_bd.principle, "Principio Actualizado")

        delete_response = self.admin_client.delete(
            f"/api/v1/learning-objects/student-register-principles/{principle_bd.id}/"
        )
        self.assertEqual(delete_response.status_code, 200, delete_response.data)
        self.assertFalse(Principle.objects.filter(id=principle_bd.id).exists())

    def test_guideline_create_requires_admin_permissions(self):
        """Permite crear guidelines solo a admin/superuser."""
        principle = Principle.objects.create(principle="Principio para guideline")
        payload = {"guideline": "Guideline Admin", "principle": principle.id}

        teacher_response = self.teacher_client.post(
            "/api/v1/learning-objects/student-register-guideline/",
            payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/learning-objects/student-register-guideline/",
            payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 201, admin_response.data)

        super_response = self.superuser_client.post(
            "/api/v1/learning-objects/student-register-guideline/",
            {"guideline": "Guideline Super", "principle": principle.id},
            format="json",
        )
        self.assertEqual(super_response.status_code, 201, super_response.data)

    def test_guideline_update_validates_unique(self):
        """En update de guideline valida unicidad según serializer custom."""
        principle = Principle.objects.create(principle="Principio guideline update")
        first = Guideline.objects.create(guideline="Guideline Base 1", principle=principle)
        Guideline.objects.create(guideline="Guideline Base 2", principle=principle)

        duplicate_update = self.admin_client.put(
            f"/api/v1/learning-objects/student-register-guideline/{first.id}/",
            {"guideline": "Guideline Base 2"},
            format="json",
        )
        self.assertEqual(duplicate_update.status_code, 400)
        self.assertIn("guideline", duplicate_update.data)

    def test_guideline_crud_update_and_delete_as_admin(self):
        """Ejecuta update/delete de guideline con permisos admin."""
        principle = Principle.objects.create(principle="Principio guideline crud")
        guideline = Guideline.objects.create(guideline="Guideline Original", principle=principle)

        update_response = self.admin_client.put(
            f"/api/v1/learning-objects/student-register-guideline/{guideline.id}/",
            {"guideline": "Guideline Actualizada"},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        guideline.refresh_from_db()
        self.assertEqual(guideline.guideline, "Guideline Actualizada")

        delete_response = self.admin_client.delete(
            f"/api/v1/learning-objects/student-register-guideline/{guideline.id}/"
        )
        self.assertEqual(delete_response.status_code, 200, delete_response.data)
        self.assertFalse(Guideline.objects.filter(id=guideline.id).exists())

    def test_student_question_create_requires_admin_permissions(self):
        """Permite crear preguntas de estudiante solo a admin/superuser."""
        principle = Principle.objects.create(principle="Principio QA estudiante")
        guideline = Guideline.objects.create(guideline="Guideline QA estudiante", principle=principle)
        payload = self._student_question_payload(guideline.id, suffix="A1")

        teacher_response = self.teacher_client.post(
            "/api/v1/learning-objective-assessment-student/",
            payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/learning-objective-assessment-student/",
            payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 201, admin_response.data)

        super_payload = self._student_question_payload(guideline.id, suffix="A2")
        super_response = self.superuser_client.post(
            "/api/v1/learning-objective-assessment-student/",
            super_payload,
            format="json",
        )
        self.assertEqual(super_response.status_code, 201, super_response.data)

    def test_student_question_update_validates_required_fields(self):
        """En update exige campos requeridos del serializer de registro."""
        principle = Principle.objects.create(principle="Principio pregunta update")
        guideline = Guideline.objects.create(guideline="Guideline pregunta update", principle=principle)
        question = Question.objects.create(
            question="Pregunta update",
            description="Descripcion",
            metadata="metadata",
            interpreter_st_yes="si",
            interpreter_st_no="no",
            interpreter_st_partially="parcial",
            interpreter_st_not_apply="na",
            value_st_importance=1.0,
            relevance="high",
            weight=1.0,
            guideline=guideline,
        )

        invalid_update = self.admin_client.put(
            f"/api/v1/learning-objective-assessment-student/{question.id}/",
            {"question": "Solo texto"},
            format="json",
        )
        self.assertEqual(invalid_update.status_code, 400)
        self.assertIn("description", invalid_update.data)

    def test_student_question_crud_update_and_delete_as_admin(self):
        """Ejecuta update/delete de pregunta de estudiante con permisos admin."""
        principle = Principle.objects.create(principle="Principio pregunta crud")
        guideline = Guideline.objects.create(guideline="Guideline pregunta crud", principle=principle)
        question = Question.objects.create(
            question="Pregunta CRUD",
            description="Descripcion",
            metadata="metadata",
            interpreter_st_yes="si",
            interpreter_st_no="no",
            interpreter_st_partially="parcial",
            interpreter_st_not_apply="na",
            value_st_importance=1.0,
            relevance="high",
            weight=1.0,
            guideline=guideline,
        )

        update_payload = {
            "question": "Pregunta CRUD Actualizada",
            "description": "Descripcion actualizada",
            "metadata": "metadata actualizada",
            "interpreter_st_yes": "si",
            "interpreter_st_no": "no",
            "interpreter_st_partially": "parcial",
            "interpreter_st_not_apply": "na",
            "value_st_importance": 2.0,
            "weight": 1.5,
            "relevance": "medium",
        }
        update_response = self.admin_client.put(
            f"/api/v1/learning-objective-assessment-student/{question.id}/",
            update_payload,
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        question.refresh_from_db()
        self.assertEqual(question.question, "Pregunta CRUD Actualizada")

        delete_response = self.admin_client.delete(
            f"/api/v1/learning-objective-assessment-student/{question.id}/"
        )
        self.assertEqual(delete_response.status_code, 200, delete_response.data)
        self.assertFalse(Question.objects.filter(id=question.id).exists())

    def test_student_question_update_accepts_legacy_front_aliases(self):
        """Acepta aliases legacy del front en update y persiste en campos canónicos."""
        principle = Principle.objects.create(principle="Principio pregunta alias")
        guideline = Guideline.objects.create(guideline="Guideline pregunta alias", principle=principle)
        question = Question.objects.create(
            question="Pregunta Alias",
            description="Descripcion",
            metadata="metadata",
            interpreter_st_yes="si",
            interpreter_st_no="no",
            interpreter_st_partially="parcial",
            interpreter_st_not_apply="na",
            value_st_importance=1.0,
            relevance="high",
            weight=1.0,
            guideline=guideline,
        )

        # Payload que históricamente envía el front.
        update_payload = {
            "question": "Pregunta Alias Actualizada",
            "description": "Descripcion actualizada",
            "schema": "metadata actualizada",
            "interpreter_yes": "si nuevo",
            "interpreter_no": "no nuevo",
            "interpreter_partially": "parcial nuevo",
            "interpreter_not_apply": "na nuevo",
            "value_importance": 2.0,
            "weight": 1.5,
            "relevance": "medium",
        }

        update_response = self.admin_client.put(
            f"/api/v1/learning-objective-assessment-student/{question.id}/",
            update_payload,
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)

        question.refresh_from_db()
        self.assertEqual(question.question, "Pregunta Alias Actualizada")
        self.assertEqual(question.metadata, "metadata actualizada")
        self.assertEqual(question.interpreter_st_yes, "si nuevo")
        self.assertEqual(question.value_st_importance, 2.0)
