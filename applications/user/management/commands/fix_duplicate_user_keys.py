"""Asigna un `user_key` propio a los usuarios que comparten uno.

Hasta marzo de 2026 el modelo usaba `default=uuid.uuid4()`: el UUID se
calculaba una vez al arrancar el servidor y todos los usuarios registrados
hasta el siguiente reinicio recibían el mismo. El enlace al perfil público
(`/author/<user_key>`) mostraba entonces a otro docente del grupo.

En cada grupo el usuario más antiguo conserva la clave, así la clave sigue
existiendo para quien la tenga guardada (por ejemplo la integración con OER
Adapt, que solo comprueba que exista). Los demás reciben una nueva.

Se ejecuta una vez, antes de la migración que agrega `unique=True`.
"""

import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count


class Command(BaseCommand):
    """Regenera `user_key` repetidos conservando el del usuario más antiguo."""

    help = (
        "Give every user a unique user_key. In each group of users sharing a key, "
        "the oldest user keeps it and the others get a new one."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report the duplicated keys without changing anything.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        dry_run = options["dry_run"]

        duplicated_keys = list(
            User.objects.values("user_key")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .order_by("-total")
            .values_list("user_key", "total")
        )
        if not duplicated_keys:
            self.stdout.write(self.style.SUCCESS("No hay user_key repetidos."))
            return

        to_change = sum(total - 1 for _, total in duplicated_keys)
        self.stdout.write(
            f"{len(duplicated_keys)} claves repetidas; {to_change} usuarios recibirán una clave nueva."
        )
        for key, total in duplicated_keys:
            self.stdout.write(f"  {str(key)[:8]}…: {total} usuarios")

        if dry_run:
            self.stdout.write("Modo de prueba: no se cambió nada.")
            return

        with transaction.atomic():
            for key, _ in duplicated_keys:
                # El de menor id es el que se registró primero.
                user_ids = list(
                    User.objects.select_for_update()
                    .filter(user_key=key)
                    .order_by("id")
                    .values_list("id", flat=True)
                )
                for user_id in user_ids[1:]:
                    # `update` evita señales y no toca `modified`.
                    User.objects.filter(pk=user_id).update(user_key=self._new_key(User))

        self.stdout.write(self.style.SUCCESS(f"Listo: {to_change} usuarios con clave nueva."))

    @staticmethod
    def _new_key(User):
        """UUID que ningún usuario tiene todavía."""

        while True:
            key = uuid.uuid4()
            if not User.objects.filter(user_key=key).exists():
                return key
