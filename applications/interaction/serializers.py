from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.interaction.models import Interaction
from rest_framework import serializers

class InteractionAllService(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ('id','liked','viewed','user','learning_object')
    
class InteractionSerializer(serializers.Serializer):
    liked = serializers.BooleanField(default=False)
    viewed = serializers.BooleanField(default=False)
    learning_object = serializers.IntegerField(required=True)
    def validate(self, data):
        incident = LearningObjectMetadata.objects.filter(pk=int(data['learning_object']))
        if not incident:
            raise serializers.ValidationError(f"Not exist oa with code {int(data['learning_object'])}")
        return data
