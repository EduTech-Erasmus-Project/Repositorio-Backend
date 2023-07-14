from django.contrib import admin

from applications.address.models import Country, Province, City, University, Campus

# Register your models here.
admin.site.register(Country)
admin.site.register(Province)
admin.site.register(City)
admin.site.register(University)
admin.site.register(Campus)