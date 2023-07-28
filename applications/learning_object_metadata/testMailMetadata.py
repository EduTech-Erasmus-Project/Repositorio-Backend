# using SendGrid's Python Library

# https://github.com/sendgrid/sendgrid-python

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from unipath import Path
#Coneccion con los entornos virtuales
import environ
import threading

from applications.settings.models import Email

env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
#Set the project base directory
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


class SendEmailCreateOA_satisfay:
    def sendMailCreateOA(self, to_email,user,name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'learning_object_metadata', 'template', 'createOASuccessfullAdmin.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)
            new_message_html = new_message_html.replace('{HOST}', env('DOMAIN_HOST_ROA'))
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver,args=[msg])
            hilo1_email.start()

        except Exception as e:
            print(e)

class SendEmailCreateOA_not_satisfy:
    def sendMail_Not_Satisfay_Admin(self, to_email,user,name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'learning_object_metadata', 'template',
                                      'createOANotSuccessfullAdmin.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)
            new_message_html = new_message_html.replace('{HOST}', env('DOMAIN_HOST_ROA'))
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver,args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)

class SendEmailCreateOA_not_satisfy_User:
    def sendMail_Not_Satisfay_User(self, to_email,user,name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'learning_object_metadata', 'template',
                                      'createOANotSuccessfullUSER.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver,args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)

class SendEmailCreateOA_satisfy_User:
    def sendMail_Satisfay_User(self, to_email,user,name_oa):
        try:
            path_email = os.path.join(BASE_DIR, 'applications', 'learning_object_metadata', 'template',
                                      'createOASuccessfullUSER.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            new_message_html = message_html.replace('{NAME_USER}', user)
            new_message_html = new_message_html.replace('{NAME_OA}', name_oa)

            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = 'Repositorio de Objetos de Aprendizaje - ROA 🚀'
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', "utf-8"))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver,args=[msg])
            hilo1_email.start()
        except Exception as e:
            print(e)

def smt_send_email_to_receiver(msg):
    """
        Funcion para abrir una sesion en smt y enviar el mesanje
    """
    email_settings = Email.objects.first()
    smtphost = email_settings.host
    password = email_settings.decrypt_password()
    username = email_settings.username
    port = email_settings.port
    msg['From'] = email_settings.email_from

    """server = smtplib.SMTP(smtphost)
    server.starttls()
    server.login(username, password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()"""

    session = smtplib.SMTP(smtphost, port)
    session.starttls()
    session.login(username, password)
    session.sendmail(msg['From'], msg['To'], msg.as_string())
    session.quit()