# using SendGrid's Python Library

# https://github.com/sendgrid/sendgrid-python

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class SendMail:
    def sendMailTest(self,to_email,url,user):
        message = Mail(
        from_email='repositorio@edutech-project.org',
        to_emails=to_email,
        subject='Resetear tu contraseña',
        html_content="""
        <strong>Hola {user}</strong>
        <br />
        <p>Está recibiendo este correo electrónico por que ha solicitado un cambio de contraseña en tu repositorio.</p>
        <br />
        <a href="{url}">Cambiar contraseña</a>
        <br />
        <P>Si no ha solicitado una nueva contraseña, por favor ignore este mensaje. Su contraseña actual no cambiará.</P>
        """.format(url=url,user=user))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
            #print(response.status_code)
            #print(response.body)
            #print(response.headers)
        except Exception as e:
            print(e)


class SendEmailCreateUser:
    def sendMailCreate(self, to_email,user):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Bienvenido al repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
               <strong>Hola {user}</strong>
               <br />
               <p>¡Grandes noticias! Te has registrado en nuestro repositorio de Objetos de Aprendizaje - ROA. 
               Puedes revisar todos los objetos de aprendizaje que se encuentran 
               en nuestro repositorio y además interactuar
                con nuestra aplicación de manera fácil y accesible.</p>
               <p>Saludos,</p>
                <br />
               <P style ="font-weight: bolder;"><a style="color: gray;" href ="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
               """.format(user=user))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)

class SendEmailCreateUserCheck:
    def sendMailCreateCheckAdmin(self, to_email,user):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Bienvenido al repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
               <strong>Hola {user}</strong>
               <br />
               <p>¡Grandes noticias! Te has registrado en nuestro repositorio de Objetos de Aprendizaje - ROA. 
               Puedes revisar todos los objetos de aprendizaje que se encuentran 
               en nuestro repositorio y además interactuar
                con nuestra aplicación de manera fácil y accesible.</p>
                <p style="font-style: italic;"> Su cuenta se encuentra en revisión, espere hasta que el administrador la apruebe.</p>
               <p>Saludos,</p>
                <br />
               <P style =" font-weight: bolder;"><a style="color: gray;" href="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
               """.format(user=user))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)

class SendEmailCreateUserCheck_Expert:
    def sendMailCreate_Expert(self, to_email,user):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Bienvenido al repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
               <strong>Hola {user}</strong>
               <br />
               <p>¡Grandes noticias! Te has registrado en nuestro repositorio de Objetos de Aprendizaje - ROA. 
               Puedes revisar todos los objetos de aprendizaje que se encuentran 
               en nuestro repositorio y además interactuar
                con nuestra aplicación de manera fácil y accesible. 
                Recuerda que puedes descargarte los objetos de aprendizaje y 
                puedes llevar a cabo su evolución.</p>              
               <p>Saludos,</p>
                <br />
               <P style =" font-weight: bolder;"><a style="color: gray;" href="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
               """.format(user=user))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)

class SendEmailCreateUserCheck_Admin_to_Expert:
    def sendMailCreate_Admin_to_Expert(self, to_email,user):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Bienvenido al repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
               <strong>Hola {user}</strong>
               <br />
               <p>¡Grandes noticias! Te has registrado en nuestro repositorio de Objetos de Aprendizaje - ROA. 
               Puedes revisar todos los objetos de aprendizaje que se encuentran 
               en nuestro repositorio y además interactuar
                con nuestra aplicación de manera fácil y accesible. 
                Recuerda que puedes descargarte los objetos de aprendizaje y 
                puedes llevar a cabo su evolución.</p>              
               <p style="font-style: italic;"> Su cuenta se encuentra en revisión, espere hasta que el administrador la apruebe.</p>
               <p>Saludos,</p>
                <br />
               <P style =" font-weight: bolder;"><a style="color: gray;" href="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
               """.format(user=user))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)

class SendEmailConfirm:
    def sendEmailConfirmAdmin(self, to_email, user):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Bienvenido al repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
                       <strong>Hola {user}</strong>
                       <br />
                       <p>¡Grandes noticias! Tu cuenta ya se encuentra activada <a href="https://repositorio.edutech-project.org/#/login">inicia sesión </a>ahora mismo.</p>
                       <p>Saludos,</p>
                        <br />
                       <P style =" font-weight: bolder;"><a style="color: gray;" href="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
                       """.format(user=user))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)