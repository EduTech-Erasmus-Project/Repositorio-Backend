from applications.preferences.models import Preferences, PreferencesArea, PreferencesFilter, PreferencesFilterArea
from rest_framework import serializers

class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preferences
        fields = (
            '__all__'
        )

class PreferencesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preferences
        fields = (
            'id',
            'description'
        )

class PreferencesListSerializersTest(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = Preferences
        fields = (
            'id',
            'description',
            'name'
        )
    def get_name(self, obj):
        query = PreferencesFilter.objects.filter(preferences__icontains=obj.description).values('search_value')
        if query.exists():
            return query[0]['search_value']
class PreferencesAreaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferencesArea
        fields = (
            '__all__'
        )

class PreferencesFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferencesFilter
        fields = (
            'search_value',
            'preferences'
        )

class PreferencesAreaFilterSerializer(serializers.ModelSerializer):
    preferences_filter = PreferencesFilterSerializer(many=True)
    class Meta:
        model = PreferencesFilterArea
        fields = (
            'filters_area',
            'preferences_filter'
        )
        
class PreferencesByAreaSerializer(serializers.ModelSerializer):
    preferences = PreferencesListSerializer(many=True)
    class Meta:
        model = PreferencesArea
        fields = (
            'id',
            'preferences_are',
            'preferences'
        )