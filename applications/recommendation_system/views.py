
from operator import contains
from applications.recommendation_system.recommended import ItemsRecomended
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert
from applications.learning_object_metadata.serializers import LearningObjectMetadataPopularSerializer, ROANumberPaginationPopular
from django.shortcuts import render
from rest_framework.views import APIView
from applications.recommendation_system.dataset_generator import DataSetGenerator
from applications.user.mixins import IsCollaboratingExpertUser, IsStudentUser, IsTeacherUser
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)

dataset_generator = DataSetGenerator()
recommended = ItemsRecomended()

# Create your views here.
class LearningObjectRecommended(ListAPIView):
    permission_classes = (IsAuthenticated,(IsStudentUser|IsTeacherUser|IsCollaboratingExpertUser))
    serializer_class = LearningObjectMetadataPopularSerializer
    pagination_class = None
    def get_queryset(self):
        try:
            user = self.request.user
            learning_objects_recommended_by_liked=recommended.user_learning_object_recomended_liked(user)
            oa_viewed = dataset_generator.LearningObjectView(user)
            df_my_preferences = dataset_generator.user_profile_dataset(user)
            userAveragePriority = self.get_user_preferences_value(df_my_preferences.groupby('preferences_are')['priority'].sum(),df_my_preferences.groupby('preferences_are')['Total'].sum())
            learningObjectAverageArea = dataset_generator.learning_object_concept_dataset()
            learning_objects_recommended_by_expert =self.recomended(learningObjectAverageArea,userAveragePriority)
            resultRecomendations= list(set(learning_objects_recommended_by_liked) | set(learning_objects_recommended_by_expert))
            # Delete learning objects already views
            results = [i for i in resultRecomendations + oa_viewed if i not in oa_viewed or i not in oa_viewed]
            oa_recommended = EvaluationCollaboratingExpert.objects.filter(
                learning_object__id__in = results
            ).order_by('-learning_object__id').distinct('learning_object__id')[:8]
            return oa_recommended
        except:
            return []

    def recomended(self, df_oa,df_user):
        try:
            oaId = df_oa['oaId'].unique()
            df_oa = df_oa.groupby(['oaId','concept'])['average'].sum()
            learning_objects = []
            for id in oaId:
                oa = df_oa.loc[id]
                oa = oa.to_dict()
                if(oa['Nivel De Interactividad'] >= df_user[0]['Nivel De Interactividad'] and
                    oa['Recursos Digitales Auditivos'] >= df_user[1]['Recursos Digitales Auditivos'] and
                    oa['Recursos Digitales Textuales'] >= df_user[2]['Recursos Digitales Textuales'] and 
                    oa['Recursos Digitales Visuales'] >= df_user[3]['Recursos Digitales Visuales']):
                    learning_objects.append(id)
            # Delete OA already views
            # results = [i for i in learning_objects + oa_viewed if i not in learning_objects or i not in oa_viewed]
            return learning_objects
        except:
            return Exception
    def get_user_preferences_value(self,totalByUser,priority):
        try:
            result = {}
            results =[]
            areas = ['Nivel De Interactividad','Recursos Digitales Auditivos','Recursos Digitales Textuales','Recursos Digitales Visuales']
            for index,data in enumerate(zip(totalByUser.to_list(),priority.to_list(),areas)):
                result = { areas[index]: (data[1]*2)/data[0] if data[0] else 0 }
                results.append(result)
            return results
        except:
            return Exception

class DataSetGeneratorView(APIView):
    # permission_classes = (IsAuthenticated,IsStudentUser,)
    permission_classes = [AllowAny,]
    def get(self, request, format=None):
        # user = self.request.user
        # dataset_generator.user_profile_dataset(user)
        # dataset_generator.users_profile_dataset()
        # dataset_generator.learning_object_concept_dataset()
        # dataset_generator.learning_object_question_dataset()
        # df = pd.read_csv("user.csv", sep=";", quoting=3)
        return Response({"message":"Dataset successfully created","status":"Ok"}, status=HTTP_200_OK)

        