"""Pruebas de las reglas del comando `normalize_oa_age_ranges`."""

from types import SimpleNamespace

from django.test import SimpleTestCase

from applications.learning_object_metadata.management.commands.normalize_oa_age_ranges import (
    CAP_MAX,
    KEEP,
    USE_LEVEL,
    classify_age_range,
    level_age_range,
)


class ClassifyAgeRangeTests(SimpleTestCase):
    """Decide si se respeta, se recorta o se reemplaza por la edad del nivel."""

    def test_keeps_reasonable_ranges(self):
        for value in ["18-65", "5-10", "6-8", "13-18", "0-5"]:
            self.assertEqual(classify_age_range(value), KEEP, value)

    def test_uses_level_for_slider_defaults(self):
        for value in ["5-100", "5-147", "5-101"]:
            self.assertEqual(classify_age_range(value), USE_LEVEL, value)

    def test_uses_level_for_impossible_or_invalid_values(self):
        for value in ["100-100", "30-20", "", None, "abc", "18"]:
            self.assertEqual(classify_age_range(value), USE_LEVEL, value)

    def test_keeps_teacher_minimum_when_only_maximum_is_too_high(self):
        for value in ["13-100", "18-150", "96-100"]:
            self.assertEqual(classify_age_range(value), CAP_MAX, value)


class LevelAgeRangeTests(SimpleTestCase):
    """Formatea la edad típica del nivel; sin máximo se guarda como 99."""

    def test_formats_closed_and_open_ranges(self):
        self.assertEqual(level_age_range(SimpleNamespace(typical_age_min=6, typical_age_max=11)), "6-11")
        self.assertEqual(level_age_range(SimpleNamespace(typical_age_min=18, typical_age_max=None)), "18-99")

    def test_returns_none_without_typical_age(self):
        self.assertIsNone(level_age_range(SimpleNamespace(typical_age_min=None, typical_age_max=None)))
        self.assertIsNone(level_age_range(None))
