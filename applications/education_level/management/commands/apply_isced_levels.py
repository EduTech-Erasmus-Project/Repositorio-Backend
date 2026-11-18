"""Pasa el catálogo de niveles educativos a la CINE 2011 de la UNESCO.

Los niveles que ya existen se renombran (conservan su id, así sus OA y
estudiantes quedan bien); los que faltan se crean. No se borra ninguno: el OA
tiene `on_delete=CASCADE` y borrar un nivel borraría sus OA.

Cada nivel actual se busca por su nombre anterior en español y, si no
aparece, por su código CINE; así el comando se puede repetir sin duplicar.

Se ejecuta después de `migrate` (los campos `isced_code`, `typical_age_min` y
`typical_age_max` deben existir). Con `--dry-run` solo muestra los cambios.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.education_level.models import EducationLevel

# (código CINE, nombre anterior, nombre ES, nombre EN, edad mínima, edad máxima)
# Edad máxima `None` = sin límite superior. Edades típicas del sistema de Ecuador.
ISCED_LEVELS = [
    (0, None, "Educación de la primera infancia", "Early childhood education", 0, 5),
    (1, "Educación primaria", "Educación primaria", "Primary education", 6, 11),
    (2, "Escuela intermedia", "Educación secundaria baja", "Lower secondary education", 12, 14),
    (3, "Educación secundaria", "Educación secundaria alta", "Upper secondary education", 15, 17),
    (4, None, "Educación postsecundaria no terciaria", "Post-secondary non-tertiary education", 18, None),
    (5, None, "Educación terciaria de ciclo corto", "Short-cycle tertiary education", 18, None),
    (6, "División superior universitaria", "Grado en educación terciaria o nivel equivalente",
     "Bachelor's or equivalent level", 18, None),
    (7, "Profesional", "Nivel de maestría, especialización o equivalente",
     "Master's or equivalent level", 22, None),
    (8, None, "Nivel de doctorado o equivalente", "Doctoral or equivalent level", 24, None),
]


class Command(BaseCommand):
    """Renombra o crea los niveles CINE 0-8 con su edad típica."""

    help = "Rename existing education levels to ISCED 2011 (levels 0-8) and create the missing ones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report what would change.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        with transaction.atomic():
            for code, old_name, name_es, name_en, age_min, age_max in ISCED_LEVELS:
                level = None
                if old_name:
                    level = EducationLevel.objects.filter(name_es=old_name).first()
                if level is None:
                    level = EducationLevel.objects.filter(isced_code=code).first()

                new_name_es = f"CINE {code} - {name_es}"
                if level is None:
                    action = "crear"
                    level = EducationLevel(isced_code=code)
                else:
                    action = f"id {level.pk}: {level.name_es!r} ->"
                self.stdout.write(f"CINE {code} | {action} {new_name_es!r}")

                level.isced_code = code
                level.name_es = new_name_es
                level.name_en = f"ISCED {code} - {name_en}"
                level.typical_age_min = age_min
                level.typical_age_max = age_max
                if not dry_run:
                    level.save()

            if dry_run:
                transaction.set_rollback(True)

        if dry_run:
            self.stdout.write(self.style.WARNING("Sin cambios (--dry-run)."))
        else:
            self.stdout.write(self.style.SUCCESS("Catálogo actualizado a CINE 2011."))
