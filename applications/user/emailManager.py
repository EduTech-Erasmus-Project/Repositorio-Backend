# using SendGrid's Python Library

# https://github.com/sendgrid/sendgrid-python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import os
from unipath import Path
# Coneccion con los entornos virtuales
import environ

env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
# Set the project base directory
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
import base64
import threading


class SendMail:
    def sendMailTest(self, to_email, url, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'resetPassword.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{URL}', url)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = "Restablecer tu contraseña"
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print('Error al enviar el correo electronico')
            print(e)


class SendEmailCreateUser:
    def sendMailCreate(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROA.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)


class SendEmailCreateUserCheck:
    def sendMailCreateCheckAdmin(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROAReview.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)


class SendEmailCreateUserCheck_Expert:
    def sendMailCreate_Expert(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROAExpert.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)


class SendEmailCreateUserCheck_Admin_to_Expert:
    def sendMailCreate_Admin_to_Expert(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'registerROAExpertReview.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)


class SendEmailConfirm:
    def sendEmailConfirmAdmin(self, to_email, user):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'confirmAccount.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{HOST}', env('DOMAIN_HOST_ROA'))
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)

    def sendEmailContactAdmin(self, to_email_admin, name_admin, name_user, email_user, message):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'contactEmail.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', name_user)
            new_message_html = new_message_html.replace('{NAME_ADMIN}', name_admin)
            new_message_html = new_message_html.replace('{CORREO}', email_user)
            new_message_html = new_message_html.replace('{MENSAJE}', message)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email_admin
            msg['Subject'] = 'Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)

    def sendEmailTesting(self, host, username, password, emailtest, port, tls, email_from):
        try:
            message_email = """Hola este es un mensaje de prueba, generado automáticamente para probar la conexión con el 
            servidor. """
            print(message_email)
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = emailtest
            msg['Subject'] = 'Bienvenido al servicio de mensajería del Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(message_email.encode('utf-8'), 'plain', "utf-8"))
            smt_send_email_to_receiver_testing_server(host, username, password, msg, port, tls,
                                                            email_from)
        except Exception as e:
            raise e


class SendEmail_activation_email:
    def send_email_confirm_email(self, to_email, user, token):

        try:
            email_bs64 = to_email
            sample_string = email_bs64
            sample_string_bytes = sample_string.encode("ascii")
            base64_bytes = base64.b64encode(sample_string_bytes)
            base64_string = base64_bytes.decode("ascii")
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'activateAccount.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{TOKEN}', token)
            new_message_html = new_message_html.replace('{EMAIL}', base64_string)
            new_message_html = new_message_html.replace('{HOST_ROA}', env('DOMAIN_HOST_ROA'))

            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Bienvenido al Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))

            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()

        except Exception as e:
            print('El error por la conexcion', e)


class SendEmailAdminCreateUser:
    def sendMail_validate_account_teacher_Admin(self, to_email, user, name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'activateAccountAdmin_Teacher.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{HOST_ROA}', env('DOMAIN_HOST_ROA'))
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)

            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))

            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)

    def sendMail_validate_account_expert_Admin(self, to_email, user, name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'user', 'template', 'activateAccountAdmin_Expert.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{HOST_ROA}', env('DOMAIN_HOST_ROA'))
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)

            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))

            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()

        except Exception as e:
            print(e)


def smt_send_email_to_receiver(msg):
    """
        Funcion para abrir una sesion en smt y enviar el mesanje
    """
    smtphost = env('EMAIL_HOST')
    password = env('EMAIL_HOST_PASSWORD')
    username = env('EMAIL_HOST_USER')

    server = smtplib.SMTP(smtphost)
    server.starttls()
    server.login(username, password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()


def smt_send_email_to_receiver_testing_server(host,username, password, emailtest, port, tls, email_from):
    smtphost = host
    password = password
    username = username

    #server = smtplib.SMTP(smtphost, port)
    server = smtplib.SMTP(smtphost)
    server.starttls()
    server.login(username, password)
    server.sendmail(email_from, 'emarquez@ups.edu.ec', emailtest.as_string())
    server.quit()
