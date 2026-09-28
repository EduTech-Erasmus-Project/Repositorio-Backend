"""Helpers livianos del modulo `user`.

Por ahora este archivo solo conserva un wrapper minimo sobre `django.core.mail`
para algunos flujos heredados que esperan un helper estático.
"""

from django.core.mail import send_mail


class Util:
    """Agrupa helpers pequenos reutilizados por serializers y vistas legacy."""

    @staticmethod
    def send_email(data):
        """Envía un correo simple a partir de un diccionario estandarizado.

        El helper espera las llaves `email_subject`, `email_body` y `to_email`.
        """

        send_mail(
            data['email_subject'],
            data['email_body'],
            'epositorio@edutech-project.org',
            [data['to_email']],
            fail_silently=False
        )
