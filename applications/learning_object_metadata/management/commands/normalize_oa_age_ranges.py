"""Corrige el rango de edad (`educational_typicalAgeRange`) de los OA.

El formulario usaba un deslizador de 5 a 150 años con `5-100` por defecto, y
la mayoría de OA se quedaron con ese valor o con edades imposibles (`5-147`,
`100-100`). Reglas:

- vacío, con otro formato, mínima mayor que la máxima o mínima mayor a 99:
  edad típica del nivel CINE
- mínima 5 (el tope inferior del deslizador) con máxima de 100 o más, como
  `5-100` o `5-147`: el docente no la eligió, edad típica del nivel CINE
- otra mínima con máxima de 100 o más, como `13-100`: se conserva la mínima
  del docente y la máxima pasa a 99

Los rangos razonables (por ejemplo `18-65` o `5-10`) no se tocan. La edad
máxima 99 significa "sin límite superior".

Sin `--apply` solo muestra lo que cambiaría.
"""

import re
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.learning_object_metadata.models import LearningObjectMetadata

AGE_RANGE_PATTERN = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
LEGACY_SLIDER_MIN = 5
AGE_MAX = 99


KEEP = "keep"
CAP_MAX = "cap_max"
USE_LEVEL = "use_level"


def classify_age_range(age_range):
    """Decide que hacer con el rango guardado: `KEEP`, `CAP_MAX` o `USE_LEVEL`."""

    match = AGE_RANGE_PATTERN.match(age_range or "")
    if not match:
        return USE_LEVEL
    age_min, age_max = int(match.group(1)), int(match.group(2))
    if age_min > age_max or age_min > AGE_MAX:
        return USE_LEVEL
    if age_max <= AGE_MAX:
        return KEEP
    return USE_LEVEL if age_min == LEGACY_SLIDER_MIN else CAP_MAX


def level_age_range(level):
    """Rango `min-max` de la edad típica del nivel, o `None` si no la tiene."""

    if level is None or level.typical_age_min is None:
        return None
    age_max = level.typical_age_max if level.typical_age_max is not None else AGE_MAX
    return f"{level.typical_age_min}-{age_max}"


class Command(BaseCommand):
    """Pone la edad típica del nivel CINE en los OA con rangos por defecto o imposibles."""

    help = (
        "Replace default (5-100) or impossible age ranges of learning objects "
        "with the typical age of their ISCED education level."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Save the changes. Without it, only report what would change.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        changes = Counter()
        skipped = 0
        to_update = []

        queryset = LearningObjectMetadata.objects.select_related("education_levels").only(
            "id", "educational_typicalAgeRange", "education_levels"
        )
        for learning_object in queryset.iterator():
            current = learning_object.educational_typicalAgeRange
            action = classify_age_range(current)
            if action == KEEP:
                continue
            if action == CAP_MAX:
                age_min = AGE_RANGE_PATTERN.match(current).group(1)
                new_range = f"{int(age_min)}-{AGE_MAX}"
            else:
                new_range = level_age_range(learning_object.education_levels)
                if new_range is None:
                    skipped += 1
                    continue
            changes[(current, new_range)] += 1
            learning_object.educational_typicalAgeRange = new_range
            to_update.append(learning_object)

        for (current, new_range), count in sorted(changes.items(), key=lambda item: -item[1]):
            self.stdout.write(f"{count:>5} | {current!r} -> {new_range!r}")
        self.stdout.write(f"OA a corregir: {len(to_update)}")
        if skipped:
            self.stdout.write(f"OA sin edad típica en su nivel (no se tocan): {skipped}")

        if not apply:
            self.stdout.write(self.style.WARNING("Sin --apply: no se guardó nada."))
            return

        with transaction.atomic():
            LearningObjectMetadata.objects.bulk_update(
                to_update, ["educational_typicalAgeRange"], batch_size=500
            )
        self.stdout.write(self.style.SUCCESS(f"Guardados: {len(to_update)}"))
