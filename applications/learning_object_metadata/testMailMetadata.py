"""Servicios de correo ligados a la evaluación automática de metadata.

Este módulo notifica a administradores y docentes cuando un OA supera o no los
umbrales de evaluación automática/manual. Las clases conservan los nombres
heredados porque son importadas directamente desde `views.py`.
"""

import logging
import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import environ
from unipath import Path

from applications.helpers_functions.env_compat import get_domain_host_roa
from applications.settings.models import Email


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

env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


class SendEmailCreateOA_satisfay:
    """Notifica a administración cuando un OA fue aprobado automáticamente."""

    def sendMailCreateOA(self, to_email, user, name_oa):
        """Renderiza la plantilla de aprobación admin y envía el correo."""

        try:
            path_email = os.path.join(
                BASE_DIR,
                "applications",
                "learning_object_metadata",
                "template",
                "createOASuccessfullAdmin.html",
            )
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace("{NAME_USER}", user)
            new_message_html = new_message_html.replace("{NAME_OA}", name_oa)
            new_message_html = new_message_html.replace("{HOST}", get_domain_host_roa())
            msg = MIMEMultipart()

            msg["To"] = to_email
            msg["Subject"] = "Repositorio de Objetos de Aprendizaje - ROA"
            msg.attach(MIMEText(new_message_html.encode("utf-8"), "html", "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()

        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception("Error enviando correo de OA satisfactorio para administrador")


class SendEmailCreateOA_not_satisfy:
    """Notifica a administración cuando un OA no supera la evaluación."""

    def sendMail_Not_Satisfay_Admin(self, to_email, user, name_oa):
        """Renderiza la plantilla de rechazo admin y envía el correo."""

        try:
            path_email = os.path.join(
                BASE_DIR,
                "applications",
                "learning_object_metadata",
                "template",
                "createOANotSuccessfullAdmin.html",
            )
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace("{NAME_USER}", user)
            new_message_html = new_message_html.replace("{NAME_OA}", name_oa)
            new_message_html = new_message_html.replace("{HOST}", get_domain_host_roa())
            msg = MIMEMultipart()

            msg["To"] = to_email
            msg["Subject"] = "Repositorio de Objetos de Aprendizaje - ROA"
            msg.attach(MIMEText(new_message_html.encode("utf-8"), "html", "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception("Error enviando correo de OA no satisfactorio para administrador")


class SendEmailCreateOA_not_satisfy_User:
    """Notifica al docente cuando su OA no supera la evaluación."""

    def sendMail_Not_Satisfay_User(self, to_email, user, name_oa):
        """Renderiza la plantilla de rechazo al docente y envía el correo."""

        try:
            path_email = os.path.join(
                BASE_DIR,
                "applications",
                "learning_object_metadata",
                "template",
                "createOANotSuccessfullUSER.html",
            )
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace("{NAME_USER}", user)
            new_message_html = new_message_html.replace("{NAME_OA}", name_oa)
            msg = MIMEMultipart()

            msg["To"] = to_email
            msg["Subject"] = "Repositorio de Objetos de Aprendizaje - ROA"
            msg.attach(MIMEText(new_message_html.encode("utf-8"), "html", "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception("Error enviando correo de OA no satisfactorio para usuario")


class SendEmailCreateOA_satisfy_User:
    """Notifica al docente cuando su OA queda aprobado automáticamente."""

    def sendMail_Satisfay_User(self, to_email, user, name_oa):
        """Renderiza la plantilla de aprobación al docente y envía el correo."""

        try:
            path_email = os.path.join(
                BASE_DIR,
                "applications",
                "learning_object_metadata",
                "template",
                "createOASuccessfullUSER.html",
            )
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace("{NAME_USER}", user)
            new_message_html = new_message_html.replace("{NAME_OA}", name_oa)

            msg = MIMEMultipart()

            msg["To"] = to_email
            msg["Subject"] = "Repositorio de Objetos de Aprendizaje - ROA"
            msg.attach(MIMEText(new_message_html.encode("utf-8"), "html", "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception("Error enviando correo de OA satisfactorio para usuario")


class SendEmailLearningObjectReviewFindings:
    """Notifica al docente los hallazgos administrativos detectados en su OA."""

    def sendMailFindings(self, to_email, user, name_oa, findings_message):
        """Renderiza la plantilla de hallazgos y enví­a el correo al docente."""

        try:
            path_email = os.path.join(
                BASE_DIR,
                "applications",
                "learning_object_metadata",
                "template",
                "learningObjectReviewFindings.html",
            )
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace("{NAME_USER}", user)
            new_message_html = new_message_html.replace("{NAME_OA}", name_oa)
            new_message_html = new_message_html.replace("{FINDINGS_MESSAGE}", findings_message)
            new_message_html = new_message_html.replace("{HOST}", get_domain_host_roa())

            msg = MIMEMultipart()
            msg["To"] = to_email
            msg["Cc"] = INSTITUTIONAL_COPY_EMAIL
            msg["Subject"] = f"Notificación de Hallazgos {name_oa} - ROA"
            msg.attach(MIMEText(new_message_html.encode("utf-8"), "html", "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception("Error enviando correo de hallazgos administrativos del OA")


def smt_send_email_to_receiver(msg):
    """Abre la sesion SMTP usando la configuración persistida en `Email`.

    Aunque el módulo sigue leyendo `.env` por compatibilidad heredada, el envío
    real toma host, credenciales y remitente desde `applications.settings`.
    """

    email_settings = Email.objects.first()
    smtphost = email_settings.host
    password = email_settings.decrypt_password()
    username = email_settings.username
    port = email_settings.port
    msg["From"] = email_settings.email_from

    server = smtplib.SMTP(smtphost)
    server.starttls()
    server.login(username, password)
    recipients = [email.strip() for email in msg.get("To", "").split(",") if email.strip()]
    recipients.extend(email.strip() for email in msg.get("Cc", "").split(",") if email.strip())
    server.sendmail(msg["From"], recipients, msg.as_string())
    server.quit()
