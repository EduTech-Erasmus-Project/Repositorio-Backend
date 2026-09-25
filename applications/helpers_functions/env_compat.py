"""Helpers de compatibilidad para variables de entorno heredadas.

Este módulo centraliza pequeños fallbacks usados por vistas y servicios que
históricamente dependían de nombres de variables distintos según el entorno.
La idea es encapsular esa compatibilidad para no repetir condicionales en el
resto del proyecto.
"""

import os

from django.core.exceptions import ImproperlyConfigured


def _get_env_value(name):
    """Lee una variable de entorno y normaliza vacíos a `None`."""
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def get_domain_host_roa():
    """Retorna el host del ROA con compatibilidad legacy.

    Si `DOMAIN_HOST_ROA` no está configurado, usa `DOMAIN_HOST` para no romper
    flujos locales que históricamente solo definían esta última variable.
    """

    value = _get_env_value("DOMAIN_HOST_ROA")
    if value is not None:
        return value

    fallback_value = _get_env_value("DOMAIN_HOST")
    if fallback_value is not None:
        return fallback_value

    raise ImproperlyConfigured(
        "Set the DOMAIN_HOST_ROA or DOMAIN_HOST environment variable"
    )


def get_key_ref():
    """
    Retorna la clave compartida para `interaction-ref`.

    Si no existe, devuelve `None` para que la vista responda de forma
    controlada en lugar de elevar un 500.
    """
    return _get_env_value("KEY_REF")
