"""Pruebas administrativas del módulo `evaluation_collaborating_expert`.

Esta suite se enfoca en la parte de catalogo y configuración que administra el
backend para la evaluación experta:
- conceptos de evaluación
- preguntas asociadas a esos conceptos
- schemas usados por la evaluación automática de metadata

El objetivo principal es asegurar permisos, validaciones de unicidad y CRUD de
los recursos que luego consumen los flujos de evaluación del experto.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.evaluation_collaborating_expert.models import EvaluationConcept, EvaluationMetadata, EvaluationQuestion
from applications.user.models import Administrator, Teacher


class AdminCrudConceptsAndQuestionsTests(TestCase):
    """Cubre el mantenimiento administrativo de conceptos, preguntas y schemas."""

    def setUp(self):
        """Prepara clientes autenticados con tres perfiles de permisos.

        Se crean:
        - un administrador activo
        - un superusuario
        - un docente sin permisos administrativos

        Eso permite comprobar acceso permitido y denegado sin repetir login en
        cada prueba.
        """
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self._sequence = 0

        self.admin_client = self._build_authenticated_client(self._create_admin_user())
        self.superuser_client = self._build_authenticated_client(self._create_superuser_user())
        self.teacher_client = self._build_authenticated_client(self._create_teacher_user())

    def _next_email(self, prefix):
        """Genera correos únicos para evitar choques entre casos de prueba."""
        self._sequence += 1
        return f"{prefix}-{self._sequence}@example.com"

    def _build_authenticated_client(self, user):
        """Autentica un cliente via JWT y lo deja listo para requests protegidos."""
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
            observation="Admin CRUD",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin"),
            first_name="Admin",
            last_name="Crud",
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
            last_name="Crud",
            password=self.password,
        )

    def _create_teacher_user(self):
        """Crea un docente para comprobar denegación en endpoints admin."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email("teacher"),
            first_name="Teacher",
            last_name="Crud",
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def _question_payload(self, concept_id, suffix="A"):
        """Construye un payload valido para crear preguntas expertas.

        El helper evita repetir un bloque largo de campos obligatorios y hace
        visible cuales son los mínimos necesarios para el serializer de alta.
        """
        return {
            "question": f"Pregunta experta {suffix}",
            "description": "Descripcion de prueba",
            "schema": f"schema:{suffix}",
            "interpreter_yes": "si",
            "interpreter_no": "no",
            "interpreter_partially": "parcial",
            "interpreter_not_apply": "na",
            "value_importance": 1.0,
            "relevance": "high",
            "weight": 1.0,
            "code": f"QC{suffix}",
            "evaluation_concept": concept_id,
        }

    def _schema_payload(self, concept_id, suffix="A"):
        """Construye un payload valido para CRUD de schemas de metadata.

        Se usa en las pruebas de evaluación automática para no repetir el shape
        esperado por el serializer de `EvaluationMetadata`.
        """
        return {
            "schema": f"schema-{suffix}",
            "description": f"Descripcion schema {suffix}",
            "value_importance_schema": "0",
            "code": f"A{suffix}",
            "evaluation_concept": concept_id,
        }

    def test_concept_create_requires_admin_permissions(self):
        """Permite crear conceptos solo a admin/superuser y bloquea docente."""
        teacher_response = self.teacher_client.post(
            "/api/v1/object-learning-concept-evaluation/",
            {"concept": "Concepto Prohibido"},
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/object-learning-concept-evaluation/",
            {"concept": "Concepto Admin"},
            format="json",
        )
        self.assertEqual(admin_response.status_code, 201, admin_response.data)

        super_response = self.superuser_client.post(
            "/api/v1/object-learning-concept-evaluation/",
            {"concept": "Concepto Super"},
            format="json",
        )
        self.assertEqual(super_response.status_code, 201, super_response.data)

    def test_concept_create_validates_required_and_unique(self):
        """Valida campo requerido y unicidad al crear conceptos."""
        empty_response = self.admin_client.post(
            "/api/v1/object-learning-concept-evaluation/",
            {},
            format="json",
        )
        self.assertEqual(empty_response.status_code, 400)
        self.assertIn("concept", empty_response.data)

        created = self.admin_client.post(
            "/api/v1/object-learning-concept-evaluation/",
            {"concept": "Concepto Unico"},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)

        duplicate = self.admin_client.post(
            "/api/v1/object-learning-concept-evaluation/",
            {"concept": "Concepto Unico"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("concept", duplicate.data)

    def test_concept_crud_update_and_delete_as_admin(self):
        """Ejecuta update y delete de concepto con permisos de administrador."""
        concept = EvaluationConcept.objects.create(concept="Concepto Original")

        update_response = self.admin_client.put(
            f"/api/v1/object-learning-concept-evaluation/{concept.id}/",
            {"concept": "Concepto Actualizado"},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        concept.refresh_from_db()
        self.assertEqual(concept.concept, "Concepto Actualizado")

        delete_response = self.admin_client.delete(
            f"/api/v1/object-learning-concept-evaluation/{concept.id}/"
        )
        self.assertEqual(delete_response.status_code, 200, delete_response.data)
        self.assertFalse(EvaluationConcept.objects.filter(id=concept.id).exists())

    def test_question_create_requires_admin_permissions(self):
        """Permite crear preguntas expertas solo a admin/superuser."""
        concept = EvaluationConcept.objects.create(concept="Concepto Permisos QA")
        payload = self._question_payload(concept.id, suffix="P1")

        teacher_response = self.teacher_client.post(
            "/api/v1/learning-objective-assessment-questions/",
            payload,
            format="json",
        )
        self.assertEqual(teacher_response.status_code, 403)

        admin_response = self.admin_client.post(
            "/api/v1/learning-objective-assessment-questions/",
            payload,
            format="json",
        )
        self.assertEqual(admin_response.status_code, 201, admin_response.data)

        super_payload = self._question_payload(concept.id, suffix="P2")
        super_response = self.superuser_client.post(
            "/api/v1/learning-objective-assessment-questions/",
            super_payload,
            format="json",
        )
        self.assertEqual(super_response.status_code, 201, super_response.data)

    def test_question_create_validates_required_and_unique(self):
        """Valida requeridos y unicidad de código/pregunta en creación de preguntas."""
        concept = EvaluationConcept.objects.create(concept="Concepto Validacion QA")

        empty_response = self.admin_client.post(
            "/api/v1/learning-objective-assessment-questions/",
            {},
            format="json",
        )
        self.assertEqual(empty_response.status_code, 400)
        self.assertIn("question", empty_response.data)

        payload = self._question_payload(concept.id, suffix="U1")
        first_create = self.admin_client.post(
            "/api/v1/learning-objective-assessment-questions/",
            payload,
            format="json",
        )
        self.assertEqual(first_create.status_code, 201, first_create.data)

        duplicate = self.admin_client.post(
            "/api/v1/learning-objective-assessment-questions/",
            payload,
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertTrue("question" in duplicate.data or "code" in duplicate.data)

    def test_question_update_validates_required_fields(self):
        """En update exige todos los campos del serializer de registro."""
        concept = EvaluationConcept.objects.create(concept="Concepto Update QA")
        question = EvaluationQuestion.objects.create(
            question="Pregunta Update QA",
            description="Desc",
            schema="schema:update",
            interpreter_yes="si",
            interpreter_no="no",
            interpreter_partially="parcial",
            interpreter_not_apply="na",
            value_importance=1.0,
            relevance="high",
            weight=1.0,
            code="QUPD",
            evaluation_concept=concept,
        )

        invalid_update = self.admin_client.put(
            f"/api/v1/learning-objective-assessment-questions/{question.id}/",
            {"question": "Faltan campos"},
            format="json",
        )
        self.assertEqual(invalid_update.status_code, 400)
        self.assertIn("description", invalid_update.data)

    def test_question_crud_update_and_delete_as_admin(self):
        """Ejecuta update y delete de pregunta experta con permisos admin."""
        concept = EvaluationConcept.objects.create(concept="Concepto CRUD QA")
        question = EvaluationQuestion.objects.create(
            question="Pregunta CRUD QA",
            description="Desc",
            schema="schema:crud",
            interpreter_yes="si",
            interpreter_no="no",
            interpreter_partially="parcial",
            interpreter_not_apply="na",
            value_importance=1.0,
            relevance="high",
            weight=1.0,
            code="QCRUD",
            evaluation_concept=concept,
        )

        update_payload = {
            "question": "Pregunta CRUD QA Actualizada",
            "description": "Desc actualizada",
            "schema": "schema:crud:new",
            "interpreter_yes": "si",
            "interpreter_no": "no",
            "interpreter_partially": "parcial",
            "interpreter_not_apply": "na",
            "value_importance": 2.0,
            "weight": 1.5,
            "relevance": "medium",
            "code": "QCRUDNEW",
        }
        update_response = self.admin_client.put(
            f"/api/v1/learning-objective-assessment-questions/{question.id}/",
            update_payload,
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)

        question.refresh_from_db()
        self.assertEqual(question.question, "Pregunta CRUD QA Actualizada")
        self.assertEqual(question.code, "QCRUDNEW")

        delete_response = self.admin_client.delete(
            f"/api/v1/learning-objective-assessment-questions/{question.id}/"
        )
        self.assertEqual(delete_response.status_code, 200, delete_response.data)
        self.assertFalse(EvaluationQuestion.objects.filter(id=question.id).exists())

    def test_schema_update_allows_keeping_same_schema_and_code(self):
        """El update de schema debe aceptar los mismos valores del propio registro."""
        concept = EvaluationConcept.objects.create(concept="Concepto Schema Update")
        schema = EvaluationMetadata.objects.create(
            schema="wefew",
            description="Descripcion original",
            value_importance_schema=0.0,
            code="A123",
            evaluation_concept=concept,
        )

        response = self.admin_client.put(
            f"/api/v1/learning-objective-assessment-schema/{schema.id}/",
            {
                "id": schema.id,
                "schema": "wefew",
                "description": "dewfwefwef",
                "value_importance_schema": "0",
                "code": "A123",
                "evaluation_concept": concept.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        schema.refresh_from_db()
        self.assertEqual(schema.schema, "wefew")
        self.assertEqual(schema.code, "A123")
        self.assertEqual(schema.description, "dewfwefwef")

    def test_schema_update_still_rejects_duplicate_code_from_other_record(self):
        """El ajuste del serializer no debe permitir colisionar con otro schema distinto."""
        concept = EvaluationConcept.objects.create(concept="Concepto Schema Duplicate")
        schema = EvaluationMetadata.objects.create(
            schema="schema-one",
            description="Schema one",
            value_importance_schema=0.0,
            code="A123",
            evaluation_concept=concept,
        )
        other_schema = EvaluationMetadata.objects.create(
            schema="schema-two",
            description="Schema two",
            value_importance_schema=1.0,
            code="B456",
            evaluation_concept=concept,
        )

        response = self.admin_client.put(
            f"/api/v1/learning-objective-assessment-schema/{schema.id}/",
            {
                "schema": "schema-one",
                "description": "Schema one updated",
                "value_importance_schema": "0",
                "code": other_schema.code,
                "evaluation_concept": concept.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("code", response.data)
