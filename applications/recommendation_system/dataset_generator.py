from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.interaction.models import Interaction
import numpy as np
import pandas as pd
import json
from applications.user.models import Student
from applications.preferences.models import Preferences, PreferencesArea
from applications.evaluation_collaborating_expert.models import (
    EvaluationConcept, 
    EvaluationQuestion, 
    EvaluationCollaboratingExpert, 
    EvaluationConceptQualification, 
    EvaluationQuestionsQualification
)

class DataSetGenerator():
    def learning_object_concept_dataset(self):
        try:
            df_oa = pd.DataFrame(list(EvaluationCollaboratingExpert.objects.all().values('id','learning_object')))
            df_concept_califiers = pd.DataFrame(list(EvaluationConceptQualification.objects.all().values('id','evaluation_concept','evaluation_collaborating_expert','average')))
            df_concept = pd.DataFrame(list(EvaluationConcept.objects.all().values('id','concept')))

            df_oa_concept_scores = pd.merge(left=df_concept_califiers,right=df_concept, left_on='evaluation_concept', right_on='id',how="inner")
            dataset_ = pd.merge(left=df_oa_concept_scores,right=df_oa, left_on='evaluation_collaborating_expert', right_on='id',how="inner"
            ).drop(['id_x','evaluation_concept','evaluation_collaborating_expert','id_y','id'],axis=1).rename({'learning_object':'oaId'},axis =1)
            dataset = dataset_.groupby(["oaId",'concept'],as_index=False).agg('mean')
            dataset = dataset.sort_values('oaId')
            # oaId = dataset.oaId.unique()
            # concept = dataset_.concept.unique()
            # df = pd.DataFrame(columns=concept,index = oaId)
            # for x in oaId:
            #     var = dataset.loc[dataset.oaId==x,['average']]
            #     df.loc[x]=var['average'].values
            # dataset = dataset.replace([1, 2], [0.5, 1])
            # df = df.rename_axis('oaId')
            # df.loc[(df['Recursos Digitales Textuales'] > 0), 'Recursos Digitales Textuales'] = 0
            # df.loc[(df['Recursos Digitales Textuales'] > 1.5), 'Recursos Digitales Textuales'] = 1
            # df.reset_index().to_csv('oa_concept.csv',sep = ';', index=False,encoding="utf-8")
            # data = pd.read_csv("oa_concept.csv", sep=";", quoting=3)
            return dataset
        except:
            return Exception


    def learning_object_question_dataset(self):
        df_oa = pd.DataFrame(list(EvaluationCollaboratingExpert.objects.all().values('id','learning_object'))).rename({'learning_object':'oaId'},axis=1)
        df_oa_concept = pd.DataFrame(list(EvaluationConceptQualification.objects.all().values('id','evaluation_collaborating_expert'))).rename({'evaluation_collaborating_expert':'oaId'},axis=1)
        df_oa_question_qualified = pd.DataFrame(list(EvaluationQuestionsQualification.objects.all().values('id','concept_evaluations','evaluation_question','qualification')))
        df_oa_question = pd.DataFrame(list(EvaluationQuestion.objects.all().values('id','description','schema','code')))
        
        dataset_oa = pd.merge(left=df_oa,right=df_oa_concept, left_on='id', right_on='oaId',how="inner"
        ).drop(['oaId_y'],axis=1).rename({'oaId_x':'oaId','id_y':'questionId'},axis=1)
        dataFrame = pd.merge(left=dataset_oa,right=df_oa_question_qualified, left_on='questionId', right_on='concept_evaluations',how="inner")
        df = pd.merge(left=dataFrame,right=df_oa_question, left_on='evaluation_question', right_on='id',how="inner"
        ).drop(['id_x','questionId','id_y','evaluation_question','concept_evaluations'],axis=1)
        df = df.groupby(["oaId","code"],as_index=False).agg('mean')
        df = df.sort_values('oaId')
        df['qualification'] = df['qualification'].round().astype(int)
        # dataset = dataset.rename_axis('loId')
        # dataset.reset_index().to_csv('learning_object_question.csv',sep = ';', index=False,encoding="ISO-8859-1")
        # df = pd.read_csv("learning_object_question.csv", sep=";", quoting=3)
        return df

    def user_profile_dataset(self, user):
        try:
            df_student = pd.DataFrame(list(Student.objects.filter(id=user.student.id).values('id','preferences')))
            df_preferences = pd.DataFrame(list(Preferences.objects.all().values('id','description','priority','preferences_area')))
            df_pref_areas = pd.DataFrame(list(PreferencesArea.objects.all().values('id','preferences_are')))
            df = pd.merge(left=df_student,right=df_preferences, left_on='preferences', right_on='id',how="outer"
            ).drop(['preferences'], axis=1
            ).rename({'id_x':'myPref','id_y':'prefId','description':'preferences'},axis=1).fillna(0)
            df1 = pd.merge(left=df,right=df_pref_areas, left_on='preferences_area',right_on='id',how="inner")
            dataset = pd.DataFrame(df1, columns=['preferences_are','preferences','myPref','priority'])
            dataset['myPref'] = dataset['myPref'].astype(int)
            dataset['myPref'] = dataset['myPref'].mask(dataset['myPref'] > 0, 1)
            dataset['Total'] = dataset['myPref'] * dataset['priority']
            # dataset.reset_index().to_csv('user.csv',sep = ';', index=False,encoding="utf-8")
            return dataset
        except:
            return Exception
 
    def users_profile_dataset(self):
        df_student = pd.DataFrame(list(Student.objects.all().values('id','preferences')))
        df_preferences = pd.DataFrame(list(Preferences.objects.all().values('id','description','priority')))
        df = pd.merge(left=df_student,right=df_preferences, left_on='preferences', right_on='id',how="outer"
        ).drop(['preferences'], axis=1
        ).rename({'id_x':'UserId','description':'preferences'},axis=1).fillna(0)
        userId = df_student.id.unique()
        preferences = df_preferences.description
        values = df.UserId.astype(int)
        dataset = pd.DataFrame(columns=preferences,index=userId)
        lista =[]
        for x in userId:
            var = df.loc[df.UserId==x,['UserId','id_y']]
            var = var['id_y'].values
            var = var.tolist()
            lista.append(var)
        for i,u in zip(range(len(lista)),userId):
            values = np.zeros(len(preferences)+1)
            values[lista[i]]=1
            pref_data = np.delete(values, 0, axis=0)
            dataset.loc[u]=pref_data
        dataset = dataset.rename_axis('UserId')
        dataset = dataset.replace([0.0, 1.0], [0, 1])
        dataset = dataset.sort_values('UserId')
        # dataset.reset_index().to_csv('users.csv',sep = ';', index=False,encoding="utf-8")
        # dataset = pd.read_csv("users.csv", sep=";", quoting=3)
        return dataset

    def learning_objects_evaluated(self):
        df_oa = pd.DataFrame(list(EvaluationCollaboratingExpert.objects.all().values('id','learning_object')))
        df_oa_concept = pd.DataFrame(list(EvaluationConceptQualification.objects.all().values('id','evaluation_collaborating_expert')))
        df_oa_evaluated = pd.DataFrame(list(EvaluationQuestionsQualification.objects.all().values('id','concept_evaluations','evaluation_question','qualification')))
        df_oa_question = pd.DataFrame(list(EvaluationQuestion.objects.all().values('id','code')))
        df_oa_metadata = pd.DataFrame(list(LearningObjectMetadata.objects.all().values('id','general_keyword','knowledge_area')))
        df_knowledArea = pd.DataFrame(list(KnowledgeArea.objects.all().values('id','name')))
        
        dataset_oa = pd.merge(left=df_oa,right=df_oa_concept, left_on='id', right_on='evaluation_collaborating_expert',how="inner"
        ).rename({'id_y':'conceptId'},axis=1)
        dataFrame = pd.merge(left=dataset_oa,right=df_oa_evaluated, left_on='conceptId', right_on='concept_evaluations',how="inner"
        ).drop(['id_x','evaluation_collaborating_expert','id'],axis=1)
        df = pd.merge(left=dataFrame,right=df_oa_question, left_on='evaluation_question', right_on='id',how="inner"
        ).drop(['conceptId','concept_evaluations','evaluation_question','id'],axis=1)
        dataset = pd.merge(left=df,right=df_oa_metadata, left_on='learning_object', right_on='id',how="inner"
        ).drop(['id'],axis=1)
        data = pd.merge(left=dataset,right=df_knowledArea, left_on='knowledge_area', right_on='id',how="inner"
        ).drop(['knowledge_area'],axis=1)
        
        evaluation_code = data.code.unique().tolist()
        oaId = data.learning_object.unique().tolist()
        general_keyword = ['general_keyword']
        knowledAreas = df_knowledArea.name.unique().tolist()
        # JOIN DATA
        df_question = pd.DataFrame(columns=evaluation_code,index = oaId)
        df_keyWord = pd.DataFrame(columns=general_keyword,index = oaId)
        df_knowledArea_data = pd.DataFrame(columns=knowledAreas,index = oaId)

        for x in oaId:
            var = data.loc[data.learning_object==x,['qualification']]
            df_question.loc[x]=var['qualification'].values

        for x in oaId:
            resp = df_oa_metadata.loc[df_oa_metadata.id==x,'general_keyword']
            df_keyWord.loc[x] = resp.values[0]

        for x in oaId:
            values = np.zeros(len(knowledAreas)+1)
            k_id = df_oa_metadata.loc[df_oa_metadata.id==x,['knowledge_area']]
            oa_knowledge_area = k_id['knowledge_area'].values
            oa_knowledge_area = oa_knowledge_area.tolist()
            values[oa_knowledge_area]=1
            pref_data = np.delete(values, 0, axis=0)
            df_knowledArea_data.loc[x]=pref_data

        frames = [df_keyWord, df_question, df_knowledArea_data]
        result = pd.concat(frames,axis=1)
        # result = result.astype(int)
        result.reset_index().to_csv('recommended_content.csv',sep = ';', index=False,encoding="utf-8")
        return result
        

    def LearningObjectView(self,user):
        df = pd.DataFrame(list(Interaction.objects.filter(user=user).values('id','learning_object')))
        if df.empty:
            return []
        learning_objects = df['learning_object']
        learning_object_view =learning_objects.tolist()
        return learning_object_view

    def user_learning_object_liked(self,user):
        try:
            df_user_interaction = pd.DataFrame(list(Interaction.objects.filter(
                user__id=user.id,
                liked = True
                ).values('user','id','learning_object','liked').order_by('-created')[:1]))
            del df_user_interaction['id']
            df_user_interaction['liked'] = df_user_interaction['liked'].astype(int)
            return df_user_interaction
        except:
            return Exception

    def learning_object_metadata(self):
        df_oa = pd.DataFrame(list(LearningObjectMetadata.objects.all().values('id','general_keyword','general_title')))
        return df_oa
    