from django.contrib import admin
from .models import (
    User,
    Student,
    Teacher,
    CollaboratingExpert,
    Administrator,
    PublicProfile,
    UserLink,
    AcademicDegree,
)


# Register your models here.
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'city', 'phone', 'observation')


class UserAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'first_name', 'last_name', 'email', 'administrator', 'student', 'teacher', 'collaboratingExpert')
    search_fields = (
        'first_name', 'last_name', 'email')


class UserLinkInline(admin.TabularInline):
    model = UserLink
    extra = 0


class AcademicDegreeInline(admin.TabularInline):
    model = AcademicDegree
    extra = 0


class PublicProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'headline', 'is_public')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    inlines = (UserLinkInline, AcademicDegreeInline)


admin.site.register(User, UserAdmin)
admin.site.register(PublicProfile, PublicProfileAdmin)
admin.site.register(Teacher)
admin.site.register(CollaboratingExpert)

admin.site.register(Student)
admin.site.register(Administrator, AdministratorAdmin)
