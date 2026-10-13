"""Actualiza a HTTPS las URLs de OAs guardadas con `http://`."""

from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError

from applications.learning_object_file.models import LearningObjectFile


class Command(BaseCommand):
    """Reescribe `LearningObjectFile.url` de `http://<host>` a `https://<host>`.

    Los OAs subidos mientras Django no reconocia el proxy HTTPS quedaron con
    URLs `http://`, que el navegador bloquea dentro del iframe del visor.
    """

    help = (
        "Rewrite LearningObjectFile.url values that start with http://<host> "
        "so they use https://<host>."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            required=True,
            help="Public host to upgrade, e.g. repositorio.edutech-project.org.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report the URLs that would change.",
        )

    def handle(self, *args, **options):
        host = options["host"].strip().lower()
        if not host or "/" in host:
            raise CommandError("--host must be a bare host name, without scheme or path.")

        dry_run = options["dry_run"]
        prefix = f"http://{host}"
        updated = 0

        candidates = LearningObjectFile.objects.filter(url__istartswith=prefix)
        for learning_object_file in candidates.iterator():
            old_url = learning_object_file.url
            # Evita tocar hosts que solo comparten prefijo (p. ej. host.org.evil).
            if (urlparse(old_url).hostname or "").lower() != host:
                continue

            new_url = "https://" + old_url[len("http://"):]
            self.stdout.write(f"[{learning_object_file.pk}] {old_url} -> {new_url}")
            if not dry_run:
                LearningObjectFile.objects.filter(pk=learning_object_file.pk).update(url=new_url)
            updated += 1

        action = "Would update" if dry_run else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} {updated} learning object URL(s)."))
