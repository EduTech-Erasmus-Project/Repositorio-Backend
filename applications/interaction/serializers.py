from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.interaction.models import Interaction, ViewInteraction
from rest_framework import serializers


class InteractionAllService(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ('id','liked','downloaded','user','learning_object')


class InteractionSerializer(serializers.Serializer):
    liked = serializers.BooleanField(default=False)
    downloaded = serializers.IntegerField(default=0)
    learning_object = serializers.IntegerField(required=True)

    def validate(self, data):
        incident = LearningObjectMetadata.objects.filter(pk=int(data['learning_object']))
        if not incident:
            raise serializers.ValidationError(f"Not exist oa with code {int(data['learning_object'])}")
        return data


class InteractionMostLiked(serializers.Serializer):
    learning_object_id = serializers.CharField()
    total = serializers.IntegerField()


class InteractionViewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewInteraction
        fields = ('view', 'learning_object')


class InteractionViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewInteraction
        fields = ('view',)