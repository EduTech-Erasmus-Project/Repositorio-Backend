"""Servicios de correo ligados al ciclo de vida de archivos OA.

Este módulo se usa para notificar al docente cuando administración elimina un
objeto de aprendizaje. La configuración SMTP real se toma desde el modelo
`applications.settings.models.Email`.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
from unipath import Path
import environ
import threading

from applications.settings.models import Email


env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

logger = logging.getLogger(__name__)
INSTITUTIONAL_COPY_EMAIL = "edutech@ups.edu.ec"

MAIL_DELIVERY_EXCEPTIONS = (
    OSError,
    smtplib.SMTPException,
    AttributeError,
    TypeError,
    ValueError,
)


def _read_html_template(path_email):
    """Lee plantillas HTML de correo forzando UTF-8."""

    with open(path_email, mode="r", encoding="utf-8") as template_file:
        return template_file.read()


class SendMail:
    """Envía correos administrativos relacionados con archivos OA."""

    def sendMailDeleteOA(self, to_email, name_user, name_oa, subject):
        """Notifica al docente que su OA fue eliminado por administración."""

        try:
            path_email = os.path.join(
                BASE_DIR,
                'applications',
                'learning_object_file',
                'template',
                'delete_learning_object_notification.html',
            )
            message_html = _read_html_template(path_email)
            message_html = message_html.replace('{NAME_USER}', name_user)
            new_message_html = message_html.replace('{NAME_OA}', name_oa)
            new_message_html = new_message_html.replace('{TEMA}', subject)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Cc'] = INSTITUTIONAL_COPY_EMAIL
            msg['Subject'] = "Eliminación del Objeto de Aprendizaje"
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error al enviar el correo de eliminacion de OA')


def smt_send_email_to_receiver(msg):
    """Abre la sesión SMTP y entrega el mensaje HTML generado.

    Aunque el módulo sigue leyendo `.env` por compatibilidad heredada, el
    envío real usa host, usuario, password y remitente desde el modelo `Email`.
    """

    email_settings = Email.objects.first()
    smtphost = email_settings.host
    password = email_settings.decrypt_password()
    username = email_settings.username
    port = email_settings.port
    msg['From'] = email_settings.email_from

    server = smtplib.SMTP(smtphost)
    server.starttls()
    server.login(username, password)
    recipients = [email.strip() for email in msg.get('To', '').split(',') if email.strip()]
    recipients.extend(email.strip() for email in msg.get('Cc', '').split(',') if email.strip())
    server.sendmail(msg['From'], recipients, msg.as_string())
    server.quit()