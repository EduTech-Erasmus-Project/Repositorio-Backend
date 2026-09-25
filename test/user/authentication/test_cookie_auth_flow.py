"""Pruebas del nuevo flujo de autenticacion por cookies HttpOnly.

La suite valida la coexistencia entre:

- login/refresh legacy por JSON + bearer
- sesion nueva basada en cookies HttpOnly
- proteccion CSRF para requests mutables que usan cookies
"""

from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from applications.user.models import Student


class CookieAuthFlowTests(TestCase):
    """Cubre login, rehidratacion, refresh y logout del flujo cookie."""

    def setUp(self):
        """Crea un usuario estudiante activo reutilizable en toda la suite."""

        self.user_model = get_user_model()
        self.password = "StrongPass123"
        self.login_url = "/api/v1/login/"
        self.user_url = "/api/v1/user/"
        self.refresh_url = "/api/v1/token/refresh/"
        self.logout_url = "/api/v1/logout/"
        self.csrf_url = "/api/v1/csrf/"
        self.access_cookie_name = settings.JWT_AUTH_COOKIE_ACCESS
        self.refresh_cookie_name = settings.JWT_AUTH_COOKIE_REFRESH
        self.csrf_cookie_name = settings.CSRF_COOKIE_NAME

        student = Student.objects.create(
            birthday=date(2000, 1, 1),
            has_disability=False,
            is_active=True,
            is_account_active=True,
        )
        self.user = self.user_model.objects.create_general_user(
            email="cookie-auth-student@example.com",
            first_name="Cookie",
            last_name="Student",
            password=self.password,
        )
        self.user.student = student
        self.user.save()

    def _login(self, client):
        """Hace login y devuelve la response para inspeccionar cookies o JWT."""

        return client.post(
            self.login_url,
            {"email": self.user.email, "password": self.password},
            format="json",
        )

    def test_login_sets_auth_and_csrf_cookies_while_preserving_legacy_json(self):
        """El login debe dejar cookies y seguir devolviendo access/refresh en JSON."""

        client = APIClient()

        response = self._login(client)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn(self.access_cookie_name, response.cookies)
        self.assertIn(self.refresh_cookie_name, response.cookies)
        self.assertIn(self.csrf_cookie_name, response.cookies)

    def test_user_endpoint_rehydrates_session_from_cookie(self):
        """`GET /user/` debe aceptar la cookie `roa_access` sin bearer."""

        client = APIClient()
        login_response = self._login(client)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)

        response = client.get(self.user_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertIn(self.csrf_cookie_name, response.cookies)

    def test_user_endpoint_keeps_legacy_bearer_compatibility(self):
        """`GET /user/` debe seguir funcionando con bearer para clientes legacy."""

        login_client = APIClient()
        login_response = self._login(login_client)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)

        legacy_client = APIClient()
        legacy_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

        response = legacy_client.get(self.user_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["email"], self.user.email)

    def test_refresh_accepts_cookie_flow_and_reissues_auth_cookies(self):
        """El refresh debe funcionar sin body cuando el cliente ya tiene cookie."""

        client = APIClient(enforce_csrf_checks=True)
        login_response = self._login(client)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)

        csrf_token = client.cookies[self.csrf_cookie_name].value
        response = client.post(
            self.refresh_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("access", response.data)
        self.assertIn(self.access_cookie_name, response.cookies)
        self.assertIn(self.refresh_cookie_name, response.cookies)
        self.assertIn(self.csrf_cookie_name, response.cookies)

    def test_refresh_legacy_body_still_works_without_cookie_csrf_flow(self):
        """La compatibilidad temporal por body debe seguir viva para clientes legacy."""

        login_client = APIClient()
        login_response = self._login(login_client)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)

        legacy_client = APIClient(enforce_csrf_checks=True)
        response = legacy_client.post(
            self.refresh_url,
            {"refresh": login_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("access", response.data)

    def test_refresh_using_cookie_without_csrf_header_is_rejected(self):
        """El refresh por cookie debe exigir CSRF para requests mutables."""

        client = APIClient(enforce_csrf_checks=True)
        login_response = self._login(client)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)

        response = client.post(self.refresh_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_logout_blacklists_refresh_clears_cookies_and_ends_cookie_session(self):
        """El logout debe limpiar cookies y dejar inutilizable la sesion del cliente."""

        client = APIClient(enforce_csrf_checks=True)
        login_response = self._login(client)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)
        previous_refresh = login_response.data["refresh"]

        csrf_token = client.cookies[self.csrf_cookie_name].value
        logout_response = client.post(
            self.logout_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK, logout_response.data)
        self.assertEqual(logout_response.data["message"], "Logout successful")
        self.assertEqual(logout_response.cookies[self.access_cookie_name].value, "")
        self.assertEqual(logout_response.cookies[self.refresh_cookie_name].value, "")

        # Simula el efecto del navegador aplicando los Set-Cookie de borrado.
        client.cookies[self.access_cookie_name] = ""
        client.cookies[self.refresh_cookie_name] = ""
        client.cookies[self.csrf_cookie_name] = ""

        user_response = client.get(self.user_url)
        self.assertEqual(user_response.status_code, status.HTTP_401_UNAUTHORIZED, user_response.data)

        refresh_response = client.post(
            self.refresh_url,
            {"refresh": previous_refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED, refresh_response.data)

    def test_csrf_bootstrap_endpoint_sets_cookie(self):
        """El endpoint `/csrf/` debe dejar la cookie lista para el frontend SPA."""

        client = APIClient()

        response = client.get(self.csrf_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn(self.csrf_cookie_name, response.cookies)
