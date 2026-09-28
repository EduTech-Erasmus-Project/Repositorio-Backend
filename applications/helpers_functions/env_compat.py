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


def get_roa_instance_name(default="ROA EduTech"):
    """Retorna el nombre visible de esta instancia ROA."""

    return _get_env_value("ROA_INSTANCE_NAME") or default


def get_roa_public_url(default="https://repositorio.edutech-project.org/"):
    """Retorna la URL publica usada para identificar esta instancia ROA."""

    return _get_env_value("ROA_PUBLIC_URL") or default


def get_contact_email_recipient(default="edutech@ups.edu.ec"):
    """Retorna el buzon institucional que recibe mensajes de contacto."""

    return _get_env_value("CONTACT_EMAIL_RECIPIENT") or default


def get_contact_email_recipient_name(default="Edutech UPS"):
    """Retorna el nombre visible del buzon institucional de contacto."""

    return _get_env_value("CONTACT_EMAIL_RECIPIENT_NAME") or default


def format_roa_email_subject(subject, instance_name=None):
    """Agrega el nombre de la instancia al final del asunto."""

    instance_name = instance_name or get_roa_instance_name()
    subject = subject.strip()
    if subject.lower().endswith(instance_name.lower()) or subject.lower().endswith(
        f"{instance_name.lower()} 🚀"
    ):
        return subject
    emoji = ""
    for suffix in (" - ROA 🚀", " - ROA"):
        if subject.endswith(suffix):
            if suffix.endswith("🚀"):
                emoji = " 🚀"
            subject = subject[: -len(suffix)]
            break
    return f"{subject} - {instance_name}{emoji}"
