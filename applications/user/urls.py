"""Rutas manuales del modulo `user`.

Este archivo reúne endpoints de autenticación, perfil, activación por correo,
contacto y reportes que no salen del `router`. También conserva compatibilidad
legacy en algunos paths duplicados con y sin slash final.
"""

from django.urls import path

from . import views


app_name = 'user_app'

# Vistas reusadas como callables para mantener el bloque de rutas más legible.
login_view = views.MyObtainTokenPairView.as_view()
user_view = views.UserAPIView.as_view()
user_count_view = views.UserCountView.as_view()
update_picture_view = views.UpdateUserProfilePicture.as_view()
get_preferences_view = views.GetStudentPreferences.as_view()
change_password_view = views.ChangePasswordView.as_view()
orcid_verify_view = views.VerifyOrcid.as_view()
total_expert_teacher_view = views.TotalExpertTeacher.as_view()
verify_email_view = views.VerifyEmail.as_view()
set_verify_view = views.set_new_token_verify.as_view()
contact_email_view = views.sendEmailContact.as_view()
report_view = views.ReportListAPIView.as_view()
teacher_delete_view = views.AdminDisaprovedTeacherDelete.as_view()
expert_delete_view = views.AdminDisaprovedCollaboratingExpertDelete.as_view()


urlpatterns = [
    # Autenticación y sesión.
    path('api/v1/login/', login_view, name='token_obtain_pair'),
    path('api/v1/csrf/', views.CsrfCookieAPIView.as_view(), name='csrf_cookie'),
    path('api/v1/token/refresh/', views.TokenRefreshSwaggerView.as_view(), name='token_refresh'),
    path('api/v1/logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('api/v1/token/verify/', views.TokenVerifySwaggerView.as_view(), name='token_verify'),
    path('api/v1/user/', user_view, name='user'),
    path('api/v1/user-count/', user_count_view),
    path('api/v1/user/photo/<int:pk>/', update_picture_view, name='upadte_picture'),
    path('api/v1/user/change_password/<int:pk>/', change_password_view, name='auth_change_password'),

    # Preferencias y datos públicos asociados al usuario.
    path('api/v1/user-preferences/email/<str:email>/', get_preferences_view, name='get_preferences'),
    path('api/v1/orcid-verify/', orcid_verify_view, name='orcid_verify'),
    path('api/v1/total-expert-teacher-approved-and-disapproved/', total_expert_teacher_view),

    # Activación y reemisión de enlaces de verificación.
    path('api/v1/email-verify/<token>/<email>', verify_email_view, name="email-verify"),
    path('api/v1/set-verify/', set_verify_view, name="set-verify"),

    # Contacto y reportes.
    path('api/v1/contact-email/', contact_email_view, name='emailContact'),
    path('api/v1/report', report_view, name="report"),

    # Eliminación administrativa de cuentas pendientes.
    path('api/v1/teacher-to-approve-delete/<pk>', teacher_delete_view, name='update_teacher_delete'),
    path('api/v1/expert-to-approve-delete/<pk>', expert_delete_view, name='delete_expert_disapproved'),
]
