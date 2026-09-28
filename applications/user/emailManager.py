"""Envio de correos transaccionales del modulo `user`.

Este archivo concentra la carga de plantillas HTML y el despacho SMTP para los
flujos principales de cuenta: bienvenida, revision administrativa, activacion,
contacto y reseteo de contrasena. Aunque conserva comentarios y estructura
heredada, el origen real de la configuracion SMTP ya no es el `.env` sino el
modelo `applications.settings.models.Email`.
"""

import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import os

from cryptography.fernet import Fernet
from unipath import Path
import environ

from applications.settings.models import Email
from applications.helpers_functions.env_compat import (
    format_roa_email_subject,
    get_domain_host_roa,
    get_roa_instance_name,
    get_roa_public_url,
)

env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
import base64
import threading

logger = logging.getLogger(__name__)

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
    """Envia el correo de reseteo de contrasena basado en plantilla HTML."""

    def sendMailTest(self, to_email, url, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'resetPassword.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{URL}', url)
            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject("Restablecer tu contraseña")
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error al enviar el correo electronico de prueba')


class SendEmailCreateUser:
    """Envia el correo de bienvenida despues de activar o crear una cuenta."""

    def sendMailCreate(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROA.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de creacion de usuario')


class SendEmailCreateUserCheck:
    """Envia el correo de cuenta en revision para docentes."""

    def sendMailCreateCheckAdmin(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROAReview.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de revision de cuenta')


class SendEmailCreateUserCheck_Expert:
    """Envia el correo de bienvenida para expertos ya aprobados."""

    def sendMailCreate_Expert(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROAExpert.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de creacion para experto')


class SendEmailCreateUserCheck_Admin_to_Expert:
    """Envia el correo de cuenta experta pendiente de revision admin."""

    def sendMailCreate_Admin_to_Expert(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROAExpertReview.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de revision admin a experto')


class SendEmailConfirm:
    """Agrupa correos de confirmacion administrativa y de contacto."""

    def sendEmailConfirmAdmin(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'confirmAccount.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{HOST}', get_domain_host_roa())
            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de confirmacion de cuenta')

    def sendEmailContactAdmin(
        self,
        to_email_admin,
        name_admin,
        name_user,
        email_user,
        message,
        roa_instance_name=None,
        roa_public_url=None,
    ):
        try:
            roa_instance_name = roa_instance_name or get_roa_instance_name()
            roa_public_url = roa_public_url or get_roa_public_url()
            safe_email_user = str(email_user).replace('\r', '').replace('\n', '').strip()
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'contactEmail.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', name_user)
            new_message_html = new_message_html.replace('{NAME_ADMIN}', name_admin)
            new_message_html = new_message_html.replace('{CORREO}', safe_email_user)
            new_message_html = new_message_html.replace('{MENSAJE}', message)
            new_message_html = new_message_html.replace('{ROA_INSTANCE_NAME}', roa_instance_name)
            new_message_html = new_message_html.replace('{ROA_PUBLIC_URL}', roa_public_url)
            msg = MIMEMultipart()
            
            msg['To'] = to_email_admin
            msg['Reply-To'] = safe_email_user
            msg['Subject'] = format_roa_email_subject(
                'Nuevo mensaje desde formulario de contacto',
                roa_instance_name,
            )
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de contacto al administrador')

    def sendEmailTesting(self, host, username, password, emailtest, port, tls, email_from):
        try:
            message_email = """Hola este es un mensaje de prueba, generado automáticamente para probar la conexión con el 
            servidor. """
            logger.info(message_email)
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = emailtest
            msg['Subject'] = format_roa_email_subject('Bienvenido al servicio de mensajería del Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(message_email, 'plain'))
            smt_send_email_to_receiver_testing_server(host, msg, username, password,port, tls)
        except MAIL_DELIVERY_EXCEPTIONS as exc:
            raise exc


class SendEmail_activation_email:
    """Envia el correo con el enlace de activacion de cuenta."""

    def send_email_confirm_email(self, to_email, user, token):

        try:
            email_bs64 = to_email
            sample_string = email_bs64
            sample_string_bytes = sample_string.encode("ascii")
            base64_bytes = base64.b64encode(sample_string_bytes)
            base64_string = base64_bytes.decode("ascii")
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'activateAccount.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{TOKEN}', token)
            new_message_html = new_message_html.replace('{EMAIL}', base64_string)
            new_message_html = new_message_html.replace('{HOST_ROA}', get_domain_host_roa())

            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))

            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()

        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de activacion de email')


class SendEmailAdminCreateUser:
    """Notifica a administradores sobre nuevas cuentas pendientes de revision."""

    def sendMail_validate_account_teacher_Admin(self, to_email, user, name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'activateAccountAdmin_Teacher.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{HOST_ROA}', get_domain_host_roa())
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)

            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))

            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de validacion de cuenta docente')

    def sendMail_validate_account_expert_Admin(self, to_email, user, name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'activateAccountAdmin_Expert.html')
            message_html = _read_html_template(path_email)
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{HOST_ROA}', get_domain_host_roa())
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)

            msg = MIMEMultipart()
            
            msg['To'] = to_email
            msg['Subject'] = format_roa_email_subject('Repositorio de Objetos de Aprendizaje - ROA 🚀')
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))

            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()

        except MAIL_DELIVERY_EXCEPTIONS:
            logger.exception('Error enviando correo de validacion de cuenta experta')


def smt_send_email_to_receiver(msg):
    """Abre una sesion SMTP usando la configuracion persistida en `Email`."""

    email_settings = Email.objects.first()
    smtphost = email_settings.host
    password = email_settings.decrypt_password()
    username = email_settings.username
    msg['From'] = email_settings.email_from

    server = smtplib.SMTP(smtphost)
    server.starttls()
    server.login(username, password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()


def smt_send_email_to_receiver_testing_server(host, msg, username, password, port, tls, ):
    """Envia un correo de prueba usando credenciales proporcionadas en runtime."""

    smtphost = host
    password = password
    username = username

    server = smtplib.SMTP(smtphost)
    server.starttls()
    server.login(username, password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
