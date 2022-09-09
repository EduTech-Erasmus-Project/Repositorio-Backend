from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/user-management', views.ManagementUserView, basename='user')
router.register(r'api/v1/management-administrator', views.UserAdminView, basename='admin')
router.register(r'api/v1/management-superuser', views.AdminListAdministrador, basename='superuser')
router.register(r'api/v1/teacher-expert-to-approve', views.AdminDisaprovedTeacherCollaboratingExpert, basename='update_disapproved')
router.register(r'api/v1/expert-to-approve', views.AdminDisaprovedCollaboratingExpert, basename='update_disapproved')
router.register(r'api/v1/teacher-expert-approved', views.AdminAprovedTeacherCollaboratingExpert, basename='update_aproved')
router.register(r'api/v1/student-list/by-admin', views.AdminListStudent, basename='list_student')
router.register(r'api/v1/teacher-list/by-admin', views.AdminListTeacher, basename='list_teacher')
router.register(r'api/v1/expert-collaborator-list', views.AdminListCollaboratingExpert, basename='list_collaborating_expert')
urlpatterns = router.urls