"""Pruebas para filtros `query` en listados administrativos de usuarios."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.user.models import Administrator, CollaboratingExpert, Student, Teacher
from applications.user.views import (
    AdminAprovedCollaboratingExpert,
    AdminAprovedTeacher,
    AdminDisaprovedCollaboratingExpert,
    AdminDisaprovedTeacher,
    AdminListStudent,
)


class AdminUserQueryFilterTests(TestCase):
    """Valida el filtro por texto libre en endpoints administrativos paginados."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self.sequence = 0
        self.admin_user = self._create_admin_user()

    def _next_email(self, prefix):
        self.sequence += 1
        return f"{prefix}-{self.sequence}@example.com"

    def _create_admin_user(self):
        administrator = Administrator.objects.create(
            country="EC",
            city="Quito",
            phone=999999999,
            observation="Admin query filters",
            is_active=True,
        )
        user = self.user_model.objects.create_admin_user(
            email=self._next_email("admin-query"),
            first_name="Admin",
            last_name="Query",
            password=self.password,
        )
        user.administrator = administrator
        user.save()
        return user

    def _create_teacher_user(self, *, first_name, last_name, email_prefix, is_active):
        teacher = Teacher.objects.create(is_active=is_active, is_account_active=is_active)
        user = self.user_model.objects.create_general_user(
            email=self._next_email(email_prefix),
            first_name=first_name,
            last_name=last_name,
            password=self.password,
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_expert_user(self, *, first_name, last_name, email_prefix, is_active):
        expert = CollaboratingExpert.objects.create(
            expert_level="Alto",
            academic_profile="Perfil",
            is_active=is_active,
            is_account_active=is_active,
        )
        user = self.user_model.objects.create_general_user(
            email=self._next_email(email_prefix),
            first_name=first_name,
            last_name=last_name,
            password=self.password,
        )
        user.collaboratingExpert = expert
        user.save()
        return user

    def _create_student_user(self, *, first_name, last_name, email_prefix):
        student = Student.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email=self._next_email(email_prefix),
            first_name=first_name,
            last_name=last_name,
            password=self.password,
        )
        user.student = student
        user.save()
        return user

    def _list_response(self, viewset_cls, path, query):
        request = self.factory.get(path, {"page": 1, "query": query})
        force_authenticate(request, user=self.admin_user)
        view = viewset_cls.as_view({"get": "list"})
        return view(request)

    def _assert_paginated_query_response(self, response, expected_email):
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], expected_email)

    def test_teacher_to_approve_filters_before_paginating(self):
        expected = self._create_teacher_user(
            first_name="Juan",
            last_name="Pendiente",
            email_prefix="teacher-pending-juan",
            is_active=False,
        )
        self._create_teacher_user(
            first_name="Maria",
            last_name="Pendiente",
            email_prefix="teacher-pending-maria",
            is_active=False,
        )

        response = self._list_response(
            AdminDisaprovedTeacher,
            "/api/v1/teacher-to-approve/",
            "juan",
        )

        self._assert_paginated_query_response(response, expected.email)

    def test_teacher_approved_filters_before_paginating(self):
        expected = self._create_teacher_user(
            first_name="Ana",
            last_name="Juarez",
            email_prefix="teacher-approved-ana",
            is_active=True,
        )
        self._create_teacher_user(
            first_name="Pedro",
            last_name="Ramirez",
            email_prefix="teacher-approved-pedro",
            is_active=True,
        )

        response = self._list_response(
            AdminAprovedTeacher,
            "/api/v1/teacher-approved/",
            "juar",
        )

        self._assert_paginated_query_response(response, expected.email)

    def test_expert_to_approve_filters_before_paginating(self):
        expected = self._create_expert_user(
            first_name="Lucia",
            last_name="Mendez",
            email_prefix="expert-pending-lucia",
            is_active=False,
        )
        self._create_expert_user(
            first_name="Carlos",
            last_name="Suarez",
            email_prefix="expert-pending-carlos",
            is_active=False,
        )

        response = self._list_response(
            AdminDisaprovedCollaboratingExpert,
            "/api/v1/expert-to-approve/",
            "lucia",
        )

        self._assert_paginated_query_response(response, expected.email)

    def test_expert_approved_filters_before_paginating(self):
        expected = self._create_expert_user(
            first_name="Rosa",
            last_name="Approved",
            email_prefix="expert-approved-rosa",
            is_active=True,
        )
        self._create_expert_user(
            first_name="Diego",
            last_name="Approved",
            email_prefix="expert-approved-diego",
            is_active=True,
        )

        response = self._list_response(
            AdminAprovedCollaboratingExpert,
            "/api/v1/expert-approved/",
            "rosa",
        )

        self._assert_paginated_query_response(response, expected.email)

    def test_student_list_by_admin_filters_before_paginating(self):
        expected = self._create_student_user(
            first_name="Mario",
            last_name="Student",
            email_prefix="student-mario",
        )
        self._create_student_user(
            first_name="Elena",
            last_name="Student",
            email_prefix="student-elena",
        )

        response = self._list_response(
            AdminListStudent,
            "/api/v1/student-list/by-admin/",
            "mario",
        )

        self._assert_paginated_query_response(response, expected.email)
