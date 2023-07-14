from django.core.mail import send_mail
# from sendgrid.helpers.mail import Mail
# repositorio@edutech-project.org
class Util:
    @staticmethod
    def send_email(data):
        send_mail(data['email_subject'], data['email_body'], 'epositorio@edutech-project.org', [data['to_email']], fail_silently=False)

# import os
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail

# message = Mail(
#     from_email='from_email@example.com',
#     to_emails='to@example.com',
#     subject='Sending with Twilio SendGrid is Fun',
#     html_content='<strong>and easy to do anywhere, even with Python</strong>')
# try:
#     sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
#     response = sg.send(message)
#     print(response.status_code)
#     print(response.body)
#     print(response.headers)
# except Exception as e:
#     print(e.message)