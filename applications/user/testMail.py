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
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e)
        