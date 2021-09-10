from .models import Preferences, PreferencesArea, PreferencesFilter, PreferencesFilterArea
from django.contrib import admin

# Register your models here.
admin.site.register(Preferences)
admin.site.register(PreferencesArea)
admin.site.register(PreferencesFilterArea)
admin.site.register(PreferencesFilter)