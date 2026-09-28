"""Rutas manuales del módulo de configuración operativa.

Este archivo agrupa endpoints administrativos para:
- configuración del servidor de correo
- administración de dominios permitidos o restringidos
- prueba de conexión SMTP
- políticas de registro por tipo de usuario
"""

from django.urls import path, include
from . import views

app_name = 'settings'

email_settings_view = views.EmailListCreateAPIView.as_view()
email_domain_view = views.EmailDomainListCreateAPIView.as_view()
email_domain_active_view = views.EmailDomainListListAPIView.as_view()
email_domain_detail_view = views.EmailDomainListView.as_view()
email_domain_update_view = views.EmailDomainUpdateView.as_view()
email_testing_view = views.sendEmailTestingConecction.as_view()
option_register_view = views.OptionRegisterEmailExtensionView.as_view()
user_type_option_view = views.UserTypeOptionView.as_view()
user_type_option_update_view = views.UserTypeOptionUpdateView.as_view()

urlpatterns = [
    # Configuración SMTP persistida.
    path('api/v1/settings/email/', email_settings_view),

    # Dominios de correo y sus variantes legacy con slash final.
    path('api/v1/settings/email-domain/', email_domain_view),
    path('api/v1/settings/email-domain/active', email_domain_active_view),
    path('api/v1/settings/email-domain/<pk>', email_domain_detail_view),
    path('api/v1/settings/email-domain-update/<pk>', email_domain_update_view),

    # Prueba de conexión y reglas globales de registro.
    path('api/v1/settings/email-testing/', email_testing_view),
    path('api/v1/settings/option-register/', option_register_view),
    path('api/v1/settings/type-user-option-register/', user_type_option_view),
    path('api/v1/settings/type-user-option-register-update/<pk>', user_type_option_update_view),

]
