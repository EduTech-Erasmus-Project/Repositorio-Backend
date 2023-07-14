from django.contrib import admin
from .models import (
    User,
    Student,
    Teacher,
    CollaboratingExpert,
    Administrator
)


# Register your models here.
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'city', 'phone', 'observation')


class UserAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'first_name', 'last_name', 'email', 'administrator', 'student', 'teacher', 'collaboratingExpert')
    search_fields = (
        'first_name', 'last_name', 'email')


admin.site.register(User, UserAdmin)
admin.site.register(Teacher)
admin.site.register(CollaboratingExpert)

admin.site.register(Student)
admin.site.register(Administrator, AdministratorAdmin)
