"""Pruebas del comando que corrige `user_key` repetidos.

En producción hay usuarios antiguos que comparten `user_key` (se generaba con
`uuid.uuid4()` una vez por arranque del servidor). El comando debe dejar a
cada usuario con una clave propia, conservando la del más antiguo de cada
grupo. La base de pruebas ya tiene `unique=True`, así que cada prueba quita la
restricción dentro de su transacción para poder recrear los duplicados.
"""

import uuid
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.db.models import Count
from django.test import TestCase


class FixDuplicateUserKeysTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self._drop_unique_user_key()
        self.shared = uuid.uuid4()
        self.users = [self._create_user(index) for index in range(4)]
        # Tres comparten clave, como en producción; el cuarto ya tiene la suya.
        self.User.objects.filter(pk__in=[user.pk for user in self.users[:3]]).update(user_key=self.shared)
        for user in self.users:
            user.refresh_from_db()

    def _drop_unique_user_key(self):
        """Quita la restricción unique de `user_key` (se revierte al terminar la prueba)."""
        table = self.User._meta.db_table
        with connection.cursor() as cursor:
            # Postgres no altera una tabla con restricciones diferidas pendientes
            # en la transacción de la prueba; se aplican antes.
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            constraints = connection.introspection.get_constraints(cursor, table)
            for name, info in constraints.items():
                if info["columns"] == ["user_key"] and info["unique"] and not info["primary_key"]:
                    cursor.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{name}"')

    def _create_user(self, index):
        return self.User.objects.create_general_user(
            email=f"user-key-{index}@example.com",
            first_name="Usuario",
            last_name=str(index),
            password="StrongPass123",
        )

    def _run(self, *args):
        out = StringIO()
        call_command("fix_duplicate_user_keys", *args, stdout=out)
        return out.getvalue()

    def test_oldest_user_keeps_the_key_and_the_others_get_new_ones(self):
        untouched_key = self.users[3].user_key

        output = self._run()

        for user in self.users:
            user.refresh_from_db()
        self.assertEqual(self.users[0].user_key, self.shared)
        self.assertNotEqual(self.users[1].user_key, self.shared)
        self.assertNotEqual(self.users[2].user_key, self.shared)
        self.assertEqual(self.users[3].user_key, untouched_key)
        self.assertFalse(
            self.User.objects.values("user_key").annotate(total=Count("id")).filter(total__gt=1).exists()
        )
        self.assertIn("2 usuarios", output)

    def test_dry_run_changes_nothing(self):
        output = self._run("--dry-run")

        self.assertEqual(self.User.objects.filter(user_key=self.shared).count(), 3)
        self.assertIn("no se cambió nada", output)

    def test_running_twice_is_harmless(self):
        self._run()

        output = self._run()

        self.assertIn("No hay user_key repetidos", output)

    def test_model_declares_user_key_unique(self):
        """La migración del modelo agrega la restricción para que no se repita."""
        self.assertTrue(self.User._meta.get_field("user_key").unique)
