from django.test import TestCase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
from unipath import Path
#Coneccion con los entornos virtuales
import environ

from applications.settings.models import Email

env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
import base64
import threading

class SendMail:
    def sendMailDeleteOA(self, to_email,name_user, name_oa, subject):
        try:
            path_email=os.path.join(BASE_DIR,'applications','learning_object_file','email.html')
            message_html = open(path_email, mode="r")
            message_html = message_html.read()
            message_html = message_html.replace('{NAME_USER}',name_user)
            new_message_html = message_html.replace('{NAME_OA}', name_oa)
            new_message_html = new_message_html.replace('{TEMA}', subject)
            msg = MIMEMultipart()
            msg['From'] = env('EMAIL_FROM')
            msg['To'] = to_email
            msg['Subject'] = "Eliminación del Objeto de Aprendizaje"
            msg.attach(MIMEText(new_message_html.encode('utf-8'), 'html', 'utf-8'))
            hilo1_email = threading.Thread(target=smt_send_email_to_receiver, args=[msg])
            hilo1_email.start()
            pass
        except Exception as e:
            print('Error al enviar el correo electronico')
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