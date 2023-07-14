from django.urls import path, include
from . import views

app_name = 'settings'
urlpatterns = [
    path('api/v1/settings/email/', views.EmailListCreateAPIView.as_view()),
    #Dominios
    path('api/v1/settings/email-domain/', views.EmailDomainListCreateAPIView.as_view()),
    path('api/v1/settings/email-domain/active', views.EmailDomainListListAPIView.as_view()),
    path('api/v1/settings/email-domain/<pk>', views.EmailDomainListView.as_view()),
    path('api/v1/settings/email-domain-update/<pk>', views.EmailDomainUpdateView.as_view()),

    path('api/v1/settings/email-testing/', views.sendEmailTestingConecction.as_view()),
    path('api/v1/settings/option-register/', views.OptionRegisterEmailExtensionView.as_view()),
    path('api/v1/settings/type-user-option-register/', views.UserTypeOptionView.as_view()),
    path('api/v1/settings/type-user-option-register-update/<pk>', views.UserTypeOptionUpdateView.as_view()),

]
