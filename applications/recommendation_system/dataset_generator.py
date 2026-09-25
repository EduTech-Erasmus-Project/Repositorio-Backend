"""Generadores de datasets auxiliares para el sistema de recomendación.

Este módulo transforma datos del dominio en `DataFrame` de pandas con formas
concretas que otras piezas del sistema esperan consumir. En lugar de exponer
un único dataset, separa varias vistas parciales:
- promedios por concepto y OA
- calificaciones por pregunta y OA
- perfil de preferencias del usuario
- metadata base para similitud o filtrado
- interacciones vistas o liked del usuario

La mayoría de los métodos degradan a estructuras vacías con columnas estables
cuando faltan datos u ocurre un error de consulta. Eso evita que las capas de
recomendación tengan que manejar `None` o formas inconsistentes.
"""

import logging

from django.db import DatabaseError
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

logger = logging.getLogger(__name__)


class DataSetGenerator():
    """Construye datasets intermedios usados por el recommendation system.

    La clase no persiste archivos ni modelos nuevos; solo consulta tablas del
    dominio y devuelve `DataFrame` o listas ya preparadas para los cálculos de
    recomendación. Sus helpers `_empty_*` fijan contratos vacíos estables para
    que las vistas puedan degradarse a resultados vacíos sin lanzar errores.
    """

    def _empty_learning_object_concept_df(self):
        """Devuelve el esquema vacío del dataset OA-concepto-promedio."""

        return pd.DataFrame(columns=['oaId', 'concept', 'average'])

    def _empty_learning_object_question_df(self):
        """Devuelve el esquema vacío del dataset OA-pregunta-calificación."""

        return pd.DataFrame(columns=['oaId', 'code', 'qualification'])

    def _empty_user_learning_object_liked_df(self):
        """Devuelve el esquema vacío del último OA liked por un usuario."""

        return pd.DataFrame(columns=['user', 'learning_object', 'liked'])

    def _empty_learning_object_metadata_df(self):
        """Devuelve el esquema vacío de metadata base para similitud."""

        return pd.DataFrame(columns=['id', 'general_keyword', 'general_title'])

    def _empty_user_profile_df(self):
        """Devuelve el esquema vacío del perfil de preferencias del usuario."""

        return pd.DataFrame(columns=['preferences_are', 'preferences', 'myPref', 'priority', 'Total'])

    def learning_object_concept_dataset(self):
        """Arma promedios por concepto para cada OA con evaluación experta pública.

        Fuentes:
        - `EvaluationCollaboratingExpert` para enlazar evaluación con OA
        - `EvaluationConceptQualification` para obtener promedios por concepto
        - `EvaluationConcept` para traducir ids a nombres de concepto

        Devuelve un `DataFrame` con columnas `oaId`, `concept` y `average`.
        Ese resultado se usa después para comparar el perfil del usuario contra
        los promedios del OA en `LearningObjectRecommended.recomended()`.
        """

        try:
            df_oa = pd.DataFrame(
                list(
                    EvaluationCollaboratingExpert.objects.filter(
                        learning_object__public=True
                    ).values('id', 'learning_object')
                ),
                columns=['id', 'learning_object'],
            )
            df_concept_califiers = pd.DataFrame(
                list(
                    EvaluationConceptQualification.objects.all().values(
                        'id', 'evaluation_concept', 'evaluation_collaborating_expert', 'average'
                    )
                ),
                columns=['id', 'evaluation_concept', 'evaluation_collaborating_expert', 'average'],
            )
            df_concept = pd.DataFrame(
                list(EvaluationConcept.objects.all().values('id', 'concept')),
                columns=['id', 'concept'],
            )
            if df_oa.empty or df_concept_califiers.empty or df_concept.empty:
                return self._empty_learning_object_concept_df()

            df_oa_concept_scores = pd.merge(
                left=df_concept_califiers,
                right=df_concept,
                left_on='evaluation_concept',
                right_on='id',
                how="inner",
            )
            dataset_ = pd.merge(
                left=df_oa_concept_scores,
                right=df_oa,
                left_on='evaluation_collaborating_expert',
                right_on='id',
                how="inner",
            ).drop(
                ['id_x', 'evaluation_concept', 'evaluation_collaborating_expert', 'id_y', 'id'],
                axis=1,
            ).rename({'learning_object': 'oaId'}, axis=1)
            if dataset_.empty:
                return self._empty_learning_object_concept_df()
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
        except (AttributeError, TypeError, ValueError, KeyError, DatabaseError):
            logger.exception("Error construyendo learning_object_concept_dataset para recommendation_system")
            return self._empty_learning_object_concept_df()


    def learning_object_question_dataset(self):
        """Arma calificaciones promedio por pregunta para cada OA evaluado.

        Encadena evaluación experta, calificación por concepto y calificación
        por pregunta hasta obtener una tabla final con:
        - `oaId`
        - `code` de la pregunta
        - `qualification` promedio redondeado

        Este dataset no es el camino principal del endpoint actual, pero sigue
        siendo útil para flujos legacy, exploración o analítica del módulo.
        """

        try:
            df_oa = pd.DataFrame(
                list(EvaluationCollaboratingExpert.objects.all().values('id', 'learning_object')),
                columns=['id', 'learning_object'],
            ).rename({'id': 'expert_evaluation_id', 'learning_object': 'oaId'}, axis=1)
            df_oa_concept = pd.DataFrame(
                list(EvaluationConceptQualification.objects.all().values('id', 'evaluation_collaborating_expert')),
                columns=['id', 'evaluation_collaborating_expert'],
            ).rename({'id': 'concept_evaluation_id', 'evaluation_collaborating_expert': 'expert_evaluation_id'}, axis=1)
            df_oa_question_qualified = pd.DataFrame(
                list(
                    EvaluationQuestionsQualification.objects.all().values(
                        'id', 'concept_evaluations', 'evaluation_question', 'qualification'
                    )
                ),
                columns=['id', 'concept_evaluations', 'evaluation_question', 'qualification'],
            ).drop(columns=['id'])
            df_oa_question = pd.DataFrame(
                list(EvaluationQuestion.objects.all().values('id', 'code')),
                columns=['id', 'code'],
            )
            if (
                df_oa.empty
                or df_oa_concept.empty
                or df_oa_question_qualified.empty
                or df_oa_question.empty
            ):
                return self._empty_learning_object_question_df()

            dataset_oa = pd.merge(
                left=df_oa,
                right=df_oa_concept,
                on='expert_evaluation_id',
                how="inner",
            )
            if dataset_oa.empty:
                return self._empty_learning_object_question_df()
            dataFrame = pd.merge(
                left=dataset_oa,
                right=df_oa_question_qualified,
                left_on='concept_evaluation_id',
                right_on='concept_evaluations',
                how="inner",
            ).drop(columns=['concept_evaluations'])
            if dataFrame.empty:
                return self._empty_learning_object_question_df()
            df = pd.merge(
                left=dataFrame,
                right=df_oa_question,
                left_on='evaluation_question',
                right_on='id',
                how="inner",
            ).drop(columns=['expert_evaluation_id', 'concept_evaluation_id', 'evaluation_question', 'id'])
            if df.empty:
                return self._empty_learning_object_question_df()
            df = df.groupby(["oaId", "code"], as_index=False)['qualification'].mean()
            df = df.sort_values('oaId')
            df['qualification'] = df['qualification'].round().astype(int)
            # dataset = dataset.rename_axis('loId')
            # dataset.reset_index().to_csv('learning_object_question.csv',sep = ';', index=False,encoding="ISO-8859-1")
            # df = pd.read_csv("learning_object_question.csv", sep=";", quoting=3)
            return df
        except (AttributeError, TypeError, ValueError, KeyError, DatabaseError, pd.errors.MergeError):
            logger.exception("Error construyendo learning_object_question_dataset para recommendation_system")
            return self._empty_learning_object_question_df()

    def user_profile_dataset(self, user):
        """Construye el perfil ponderado de preferencias de un usuario estudiante.

        El método solo aplica si el usuario tiene perfil `student`. Combina:
        - preferencias seleccionadas por el estudiante
        - catálogo de preferencias con su prioridad
        - área a la que pertenece cada preferencia

        Devuelve un `DataFrame` con una fila por preferencia y columnas que
        permiten calcular umbrales agregados por área conceptual:
        - `preferences_are`
        - `preferences`
        - `myPref` como bandera binaria
        - `priority`
        - `Total` como producto de presencia por prioridad
        """

        try:
            student_id = getattr(getattr(user, 'student', None), 'id', None)
            if student_id is None:
                return self._empty_user_profile_df()
            df_student = pd.DataFrame(
                list(Student.objects.filter(id=student_id).values('id', 'preferences')),
                columns=['id', 'preferences'],
            )
            df_preferences = pd.DataFrame(
                list(Preferences.objects.all().values('id', 'description', 'priority', 'preferences_area')),
                columns=['id', 'description', 'priority', 'preferences_area'],
            )
            df_pref_areas = pd.DataFrame(
                list(PreferencesArea.objects.all().values('id', 'preferences_are')),
                columns=['id', 'preferences_are'],
            )
            if df_student.empty or df_preferences.empty or df_pref_areas.empty:
                return self._empty_user_profile_df()
            df = pd.merge(left=df_student,right=df_preferences, left_on='preferences', right_on='id',how="outer"
            ).drop(['preferences'], axis=1
            ).rename({'id_x':'myPref','id_y':'prefId','description':'preferences'},axis=1).fillna(0)
            df1 = pd.merge(left=df,right=df_pref_areas, left_on='preferences_area',right_on='id',how="inner")
            dataset = pd.DataFrame(df1, columns=['preferences_are','preferences','myPref','priority'])
            if dataset.empty:
                return self._empty_user_profile_df()
            dataset['myPref'] = dataset['myPref'].astype(int)
            dataset['myPref'] = dataset['myPref'].mask(dataset['myPref'] > 0, 1)
            dataset['Total'] = dataset['myPref'] * dataset['priority']
            # dataset.reset_index().to_csv('user.csv',sep = ';', index=False,encoding="utf-8")
            return dataset
        except (AttributeError, TypeError, ValueError, KeyError, DatabaseError):
            logger.exception(
                "Error construyendo el perfil de preferencias para el usuario %s",
                getattr(user, 'id', None),
            )
            return self._empty_user_profile_df()

    def users_profile_dataset(self):
        """Genera una matriz usuario-preferencia para todos los estudiantes.

        A diferencia de `user_profile_dataset`, aquí el objetivo no es calcular
        un perfil ponderado por área sino una representación binaria completa
        donde cada fila es un estudiante y cada columna una preferencia.

        El método conserva mucho estilo legacy y no tiene el mismo nivel de
        guardas que otros helpers del módulo.
        """

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
        """Construye un dataset amplio de OAs evaluados, keywords y preguntas.

        Este helper mezcla:
        - calificaciones por pregunta
        - metadata del OA
        - one-hot encoding del área de conocimiento

        El resultado está orientado a exportación o experimentación más que al
        endpoint actual de recomendaciones. Mantiene un estilo heredado basado
        en concatenar varias vistas parciales dentro de un único `DataFrame`.
        """

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
        """Devuelve la lista de ids de OAs ya vistos por el usuario.

        El endpoint de recomendaciones usa esta lista para excluir contenido que
        ya apareció en interacciones previas del usuario autenticado.
        """

        try:
            df = pd.DataFrame(
                list(Interaction.objects.filter(user=user).values('id', 'learning_object')),
                columns=['id', 'learning_object'],
            )
        except (AttributeError, TypeError, ValueError, DatabaseError):
            logger.exception(
                "Error obteniendo learning objects vistos para el usuario %s",
                getattr(user, 'id', None),
            )
            return []
        if df.empty or 'learning_object' not in df.columns:
            return []
        return df['learning_object'].tolist()

    def user_learning_object_liked(self,user):
        """Devuelve el ultimo OA marcado como liked por el usuario.

        La salida es un `DataFrame` pequeño con una sola fila como máximo. Ese
        formato se conserva porque otras partes del recommendation system lo
        consumen como dataset y no solo como un id simple.
        """

        try:
            df_user_interaction = pd.DataFrame(list(Interaction.objects.filter(
                user__id=user.id,
                liked = True
                ).values('user','id','learning_object','liked').order_by('-created')[:1]),
                columns=['user', 'id', 'learning_object', 'liked']
            )
            if df_user_interaction.empty:
                return self._empty_user_learning_object_liked_df()
            df_user_interaction = df_user_interaction.drop(columns=['id'])
            df_user_interaction['liked'] = df_user_interaction['liked'].astype(int)
            return df_user_interaction
        except (AttributeError, TypeError, ValueError, KeyError, DatabaseError):
            logger.exception(
                "Error obteniendo el ultimo learning object liked para el usuario %s",
                getattr(user, 'id', None),
            )
            return self._empty_user_learning_object_liked_df()

    def learning_object_metadata(self):
        """Devuelve metadata base de OAs públicos para similitud o ranking.

        El dataset expone solo los campos mínimos que otros algoritmos del
        modulo usan para comparar OAs o enriquecer recomendaciones:
        - `id`
        - `general_keyword`
        - `general_title`
        """

        try:
            return pd.DataFrame(
                list(
                    LearningObjectMetadata.objects.filter(public=True).values(
                        'id', 'general_keyword', 'general_title'
                    )
                ),
                columns=['id', 'general_keyword', 'general_title'],
            )
        except (AttributeError, TypeError, ValueError, DatabaseError):
            logger.exception("Error obteniendo metadata base para recommendation_system")
            return self._empty_learning_object_metadata_df()
    
