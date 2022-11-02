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


class SendEmailCreateOA_satisfay:
    def sendMailCreateOA(self, to_email,user,name_oa):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
               <strong>Hola querido administrador {user}</strong>
               <br />
               <p>¡Grandes noticias! Se subió un objeto de aprendizaje <i>{name_oa}</i> que cumple satisfactoriamente con los requisitos de metadatos. 
               Puedes revisar todos los objetos de aprendizaje que se encuentran en la lista de objetos de aprendizajes 
               <a style="color: gray;" href ="https://repositorio.edutech-project.org/#/admin/learning-object/approved">aprobados</a>.</p>
               <p>Saludos,</p>
                <br />
               <P style ="font-weight: bolder;"><a style="color: gray;" href ="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
               """.format(user=user, name_oa= name_oa))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)

class SendEmailCreateOA_not_satisfy:
    def sendMail_Not_Satisfay_Admin(self, to_email,user,name_oa):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
               <strong>Hola querido administrador {user}</strong>
               <br />
               <p>¡Se subió un objeto de aprendizaje que necesita ser aprobado <i>{name_oa}</i> ! Puedes revisar la lista de Objetos de Aprendizaje  
               <a style="color: gray;" href ="https://repositorio.edutech-project.org/#/admin/learning-object/pending">no aprobados</a>.</p>
               <p>Saludos,</p>
                <br />
               <P style =" font-weight: bolder;"><a style="color: gray;" href="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
               """.format(user=user, name_oa=name_oa))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)

class SendEmailCreateOA_not_satisfy_User:
    def sendMail_Not_Satisfay_User(self, to_email,user,name_oa):
        message = Mail(
            from_email='repositorio@edutech-project.org',
            to_emails=to_email,
            subject='Repositorio de Objetos de Aprendizaje - ROA 🚀',
            html_content="""
               <strong>Hola {user}</strong>
               <br />
               <p>¡Tu objeto de aprendizaje necesita ser aprobado! Se subió con éxito el objeto de aprendizaje 
               <i>{name_oa}</i>, ahora debes esperar hasta que el administrador lo apruebe y pueda visualizarse en la pagina de busqueda.</p>
               <p>Saludos,</p>
                <br />
               <P style =" font-weight: bolder;"><a style="color: gray;" href="https://repositorio.edutech-project.org/#/">Equipo ROA</a></P>
               """.format(user=user, name_oa=name_oa))
        try:
            sg = SendGridAPIClient('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')
            response = sg.send(message)
        except Exception as e:
            print(e)

