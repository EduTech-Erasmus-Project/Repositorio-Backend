from django.shortcuts import render
from django.db.models.signals import post_save
from applications.learning_object_metadata.serializers import LearningObjectMetadataAllSerializer, LearningObjectMetadataByExpet, ROANumberPagination
from applications.learning_object_metadata.models import LearningObjectMetadata
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated ,AllowAny
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser
from applications.user.models import User
from applications.evaluation_collaborating_expert.serializers import (
    EvaluationAutomaticEvaluationSerializer,
    EvaluationCollaboratingExpertEvaluationSerializer,
    EvaluationCollaboratingExpertSerializer,
    EvaluationConceptListSerializer,
    EvaluationConceptListSerializerSCHEMA,
    EvaluationConceptSerializer,
    EvaluationExpertCreateSerializer,
    EvaluationMetadataRegisterSerializer,
    EvaluationMetadataSerializer,
    EvaluationQuestionRegisterSerializer,
    EvaluationQuestionSerializer,
    EvaluationQuestionQualificationSerializer,
    QuestionQualificationListSerializer
)
from . models import (
    EvaluationConcept,
    EvaluationMetadata, 
    EvaluationQuestion,
    EvaluationQuestionsQualification,
    EvaluationConceptQualification,
    EvaluationCollaboratingExpert,
    MetadataAutomaticEvaluation,
    MetadataQualificationConcept
)
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
) 
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from roabackend.settings import NO, PARTIALLY, YES,CALIFICATION_OPTIONS, NOT_APPLY
# Create your views here.
# EVALUATION
class EvaluationConceptViewSet(viewsets.ModelViewSet):
    """
        Servicio crear conceptos de Objeto de Aprendizaje.
        CREATE, UPDATE & DELETE Api disponible para usurio Administrador.
        LIST (GET) Api disponible para usuario administradory experto colaborador
    """ 
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationConceptSerializer
    queryset = EvaluationConcept.objects.all()
    action_serializers = {
        'list': EvaluationConceptListSerializer,
    }
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationConceptViewSet, self).get_serializer_class()
    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar concepto
        """
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.concept = request.data['concept']
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Obtener Concepto por ID
        """
        queryset = EvaluationConcept.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationConceptListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        """
            Eliminar el concepto de evaluación
        """
        queryset = EvaluationConcept.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)

class EvaluationQuestionsViewSet(viewsets.ModelViewSet):
    """
        Servicio para crear preguntas sobre la evalucaion de los OA.
        CREATE, UPDATE & DELETE Api accesible para usuario administrador.
        LIST (GET) Api accesible para totos los usuarios 
    """
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationQuestionSerializer
    queryset = EvaluationQuestion.objects.all()
    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar pregunta
        """
        #print("entro en el original")
        queryset = EvaluationQuestion.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationQuestionRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        #print("---->>>>")
        instance.question = serializer.validated_data['question']
        instance.description = serializer.validated_data['description']
        instance.schema = serializer.validated_data['schema']
        instance.code = serializer.validated_data['code']
        ##############################################################
        instance.interpreter_yes = serializer.validated_data['interpreter_yes']
        instance.interpreter_no = serializer.validated_data['interpreter_no']
        instance.interpreter_partially = serializer.validated_data['interpreter_partially']
        instance.interpreter_not_apply = serializer.validated_data['interpreter_not_apply']
        instance.value_importance = serializer.validated_data['value_importance']
        ###############################################################
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Obtener pregunta por ID
        """
        queryset = EvaluationQuestion.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationQuestionSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        """
            Eliminar pregunta
        """
        queryset = EvaluationQuestion.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)


class EvaluationQuestionsQualificationVieeSet(viewsets.ModelViewSet):
    """
        Servicio para realizar la evalución del Objeto de Aprendizaje.
        CREATE, UPDATE & DELETE, Api accesible para usuario Experto colaborador.
        LIST (GET) Api accesible para los usuarios admintradores y Expertos colaboradores 
    """
    def get_permissions(self):
        if(self.action=='create' or self.action=='list' or self.action=='retrieve'):
            permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
        else:
            permission_classes = [IsAuthenticated,IsCollaboratingExpertUser,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationQuestionQualificationSerializer
    queryset = EvaluationQuestionsQualification.objects.all()
    action_serializers = {
        'list': QuestionQualificationListSerializer,
    }
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationConceptViewSet, self).get_serializer_class()

    def perform_create(self, serializer):
        """
            Crear los metadadtos de los OA. API acesible para usurio docentes
        """
        serializer.save(
            user_created=self.request.user
        )

class EvaluationCollaboratingExpertView(viewsets.ViewSet):
    def get_permissions(self):
        if(self.action=='create'):
            permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
        else:
            permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
        return [permission() for permission in permission_classes]

    def  create(self, request, *args, **kwargs):
        """
            Servicio para crear la evaluación correspondiente al experto.
        """
        serializer = EvaluationExpertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation_questions_ =  []
        qualifications =  []
        for result in serializer.validated_data['results']:
            evaluation_questions_.append(result['id'])
            qualifications.append(result['value'])
        user = User.objects.get(id=self.request.user.id)
        oa_is_evaluated = EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=serializer.validated_data['learning_object'],
            collaborating_expert__id=user.id
            )
        if oa_is_evaluated:
            return Response({"message": "Learning Object is already evaluated by this expert"},status=HTTP_400_BAD_REQUEST)

        learningObjectMetadata=LearningObjectMetadata.objects.get(
            id=serializer.validated_data['learning_object']
        )
        
        evaluation_questions = EvaluationQuestion.objects.filter(
             id__in=evaluation_questions_
         )
        evaluation_concept_list=[]
        for evaluation_question in evaluation_questions:
            evaluation_concept_list.append(evaluation_question.evaluation_concept.id)

        evaluation_concept_list=list(dict.fromkeys(evaluation_concept_list))
        evaluation_concepts = EvaluationConcept.objects.filter(
             id__in=evaluation_concept_list
         )
        scores = []
        # qualifications= serializer.validated_data['qualifications']
        for qualification in qualifications:
            if(qualification== CALIFICATION_OPTIONS['YES']):
                scores.append(YES)
            elif(qualification==CALIFICATION_OPTIONS['NO']):
                scores.append(NO)
            elif(qualification==CALIFICATION_OPTIONS['PARTIALLY']):
                scores.append(PARTIALLY)
            else:
                scores.append(NOT_APPLY)

        evaluationCollaboratingExpert= EvaluationCollaboratingExpert.objects.create(
            learning_object =learningObjectMetadata,
            rating = 0.0,
            observation=serializer.validated_data['observation'],
            collaborating_expert = user
        )
        ratings = 0.0
        evaluationConceptQualificationList=[]
        for evaluation_concept in evaluation_concepts:
            evaluationConceptQualification=EvaluationConceptQualification.objects.create(
                evaluation_concept=evaluation_concept,
                evaluation_collaborating_expert=evaluationCollaboratingExpert,
                average=0.0
            )
            evaluationConceptQualificationList.append(evaluationConceptQualification)
        evaluationQuestionsQualificationList = []
        cont_not_apply = 0
        for evaluation_question,qualification in zip(evaluation_questions,scores):
            for evaluationConceptQualification in evaluationConceptQualificationList:
                if(evaluationConceptQualification.evaluation_concept==evaluation_question.evaluation_concept):
                    evaluationQuestionsQualification = EvaluationQuestionsQualification.objects.create(
                            concept_evaluations=evaluationConceptQualification,
                            evaluation_question=evaluation_question,
                            qualification=qualification
                            )
                    if (qualification != -1 and evaluation_question.id != 1 and evaluation_question.id != 2 and evaluation_question.id != 3):
                        #Multiplicamos por el peso de la pregunta
                        multiplicacion = qualification * evaluation_question.weight
                        ratings = ratings + multiplicacion
                    else:
                        cont_not_apply += 1

                    evaluationQuestionsQualificationList.append(evaluationQuestionsQualification)

        updateAverage(evaluationQuestionsQualificationList,evaluationConceptQualificationList)

        evaluationCollaboratingExpert.rating=(ratings/(len(evaluationQuestionsQualificationList) - cont_not_apply))/2.4

        evaluationCollaboratingExpert.save()
        serializer = EvaluationCollaboratingExpertSerializer(evaluationCollaboratingExpert)
        return Response(serializer.data, status=HTTP_200_OK)                           

    def list(self, request):
        """
            Servicio para listar las evaluaciones de cada experto colaborador
        """
        queryset = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        )
        serializer = EvaluationCollaboratingExpertSerializer(queryset, many=True)
        return Response(serializer.data,status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para obtener una calificacion del experto colaborador
        """
        queryset = EvaluationCollaboratingExpert.objects.filter(
        collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id,
        id=pk
        )

        get_evaluation_expert = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationCollaboratingExpertSerializer(get_evaluation_expert)
        
        return Response(serializer.data, status=HTTP_200_OK)


    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actuaizar una evalución
        """
        serializer = EvaluationExpertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation_questions_ =  []
        qualifications =  []
        for result in serializer.validated_data['results']:
            evaluation_questions_.append(result['id'])
            qualifications.append(result['value'])
        scores = []
        for qualification in qualifications:
            if(qualification==CALIFICATION_OPTIONS['YES']):
                scores.append(YES)
            elif(qualification==CALIFICATION_OPTIONS['NO']):
                scores.append(NO)
            elif (qualification == CALIFICATION_OPTIONS['NOT_APPLY']):
                scores.append(NOT_APPLY)
            else:
                scores.append(PARTIALLY)
        
        #print("scores experto-->>>",scores)
        queryset = EvaluationCollaboratingExpert.objects.filter(
        collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        )
        evaluation_expert = get_object_or_404(queryset, pk=pk)
        evaluation_expert.observation=serializer.validated_data['observation']

        evaluationQuestionsQualifications = EvaluationQuestionsQualification.objects.filter(
            concept_evaluations__evaluation_collaborating_expert__id = pk
        )
        evaluationConceptQualificationList=[]
        for evaluationQuestion in evaluationQuestionsQualifications:
            evaluationConceptQualification=EvaluationConceptQualification.objects.get(
                id=evaluationQuestion.concept_evaluations.id
            )
            evaluationConceptQualificationList.append(evaluationConceptQualification)
        rating=0.0
        cont_not_apply = 0
        for evaluationQuestionsQualification,qualification in zip(evaluationQuestionsQualifications,scores):
            evaluationQuestionsQualification.qualification=qualification
            if (qualification != -1 and evaluationQuestionsQualification.evaluation_question_id !=1and evaluationQuestionsQualification.evaluation_question_id !=2and evaluationQuestionsQualification.evaluation_question_id !=3):
                #Obtenemos el peso de la pregunta
                wieght_question = EvaluationQuestion.objects.get(pk = evaluationQuestionsQualification.evaluation_question_id)
                #Multiplicamos el peso con la calificacion de la evaluacion
                multiplicacion = qualification * wieght_question.weight
                rating = rating+multiplicacion
            else:
                cont_not_apply += 1

        evaluation_expert.rating=(rating/(len(evaluationQuestionsQualifications) - cont_not_apply))/2.4

        evaluation_expert.save()
        updateAverage(evaluationQuestionsQualifications,evaluationConceptQualificationList)
        EvaluationQuestionsQualification.objects.bulk_update(evaluationQuestionsQualifications,['qualification'])
        serializer = EvaluationCollaboratingExpertSerializer(evaluation_expert)
        return Response(serializer.data ,status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """
            Servicio para eliminar una evalución
        """
        evaluationQuestionsQualifications = EvaluationQuestionsQualification.objects.filter(
            concept_evaluations__evaluation_collaborating_expert__id = pk
        )
        for evaluationQuestionsQualification in evaluationQuestionsQualifications:
            evaluationQuestionsQualification.delete()

        evaluationConceptQualifications= EvaluationConceptQualification.objects.filter(
            evaluation_collaborating_expert__id=pk
        )
        for evaluationConceptQualification in evaluationConceptQualifications:
            evaluationConceptQualification.delete()

        queryset = EvaluationCollaboratingExpert.objects.filter(
        collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        )
        evaluation_expert = get_object_or_404(queryset, pk=pk)
        evaluation_expert.delete()
        return Response({"message": "success"},status=HTTP_200_OK) 

class EvaluationQuestionsExpertView(ListAPIView):
    """
        Listar area de evaluación para el experto
    """
    permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
    serializer_class = EvaluationConceptListSerializer
    def get_queryset(self):
        return EvaluationConcept.objects.all()

class LerningObjectRated(ListAPIView):
    """
        Listar evaluación del experto
    """
    permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
    serializer_class = LearningObjectMetadataByExpet
    pagination_class = ROANumberPagination
    def get_queryset(self):
        query = EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        ).order_by('-id')
        return query

class LerningObjectNotRated(ListAPIView):
    """
        Listar Objetos de Aprendizaje no evaluados
    """
    permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    def get_queryset(self):
        query= LearningObjectMetadata.objects.filter(
            public = True
        ).exclude(
            learning_objects__collaborating_expert__collaboratingExpert__id=self.request.user.collaboratingExpert.id
        ).order_by('-id')
        return query

class ListOAEvaluatedRetriveAPIView(ListAPIView):
    """
        Listar resultado de la evaluación realizado por el experto por id del OA.
        El servicio está disponible para todos los usuarios.
    """
    permission_classes = [AllowAny]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer
    def get_queryset(self):
        id = self.kwargs['pk']
        return EvaluationCollaboratingExpert.objects.filter(
            learning_object__id=id,
        ).distinct('learning_object')
        
class ListOAEvaluatedToExpertRetriveAPIView(ListAPIView):
    """
        Listar resultado de la evaluación realizado por el experto por id del OA.
        El servicio requiere de la autenticación como experto.
    """

    permission_classes = [IsAuthenticated,IsCollaboratingExpertUser]
    serializer_class = EvaluationCollaboratingExpertEvaluationSerializer

    def get_queryset(self):
        id = self.kwargs['pk']
        print("----return",EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__id=self.request.user.id,
            learning_object__id=id,
        ).distinct('learning_object'))

        return EvaluationCollaboratingExpert.objects.filter(
            collaborating_expert__id=self.request.user.id,
            learning_object__id=id,
        ).distinct('learning_object')


def updateAverage(scoreData:list,instances:list):
    concepts = []
    concepts_ = EvaluationConcept.objects.all().values_list('concept', flat=True) 
    for concept in concepts_:
        concepts.append(concept)

    dicDta1 ={}
    dicDta2 ={}
    dicDta3 ={}
    dicDta4 ={}
    concept_1 =""
    average1 = 0.0
    concept_2 =""
    average2 = 0.0
    concept_3 =""
    average3 = 0.0
    concept_4 =""
    average4 = 0.0
    tam1=0
    tam2=0
    tam3=0
    tam4=0

    for concept in scoreData:
        if(str(concept.concept_evaluations.evaluation_concept))==concepts[0]:
            concept_1 = str(concept.concept_evaluations.evaluation_concept)
            if(concept.qualification != -1):
                average1 = average1+concept.qualification
                tam1 = tam1+1
                #print("---1",average1,"tam",tam1)
                dicDta1 = {
                    'average':average1/tam1,
                    'concept':concept_1
                }

        if(str(concept.concept_evaluations.evaluation_concept))==concepts[1]:
            concept_2 = str(concept.concept_evaluations.evaluation_concept)
            if (concept.qualification != -1):
                average2 = average2+concept.qualification
                tam2 = tam2+1
                #print("---2",average2,"tam",tam2)
                dicDta2 = {
                    'average':average2/tam2,
                    'concept':concept_2
                }
        if(str(concept.concept_evaluations.evaluation_concept))==concepts[2]:
            concept_3 = str(concept.concept_evaluations.evaluation_concept)
            if (concept.qualification != -1):
                average3 = average3+concept.qualification
                tam3 = tam3+1
                #print("---3",average3,"tam",tam3)
                dicDta3 = {
                    'average':average3/tam3,
                    'concept':concept_3
                }
        if(str(concept.concept_evaluations.evaluation_concept))==concepts[3]:
            concept_4 = str(concept.concept_evaluations.evaluation_concept)
            if (concept.qualification != -1):
                average4 = average4+concept.qualification
                tam4 = tam4+1
                #print("---4",average4,"tam",tam4)
                dicDta4 = {
                    'average':average4/tam4,
                    'concept':concept_4
                }

    for instance in instances:
        instance_update = EvaluationConceptQualification.objects.get(id=instance.id)
        if instance_update.evaluation_concept.concept == concepts[0]:
            instance_update.average = dicDta1['average']
            #print("---1.1",dicDta1['average'])
            instance_update.save()
        if instance_update.evaluation_concept.concept == concepts[1]:
            instance_update.average = dicDta2['average']
            #print("---2.1",dicDta2['average'])
            instance_update.save()
        if instance_update.evaluation_concept.concept == concepts[2]:
            instance_update.average = dicDta3['average']
            #print("---3.1",dicDta3['average'])
            instance_update.save()
        if instance_update.evaluation_concept.concept == concepts[3]:
            instance_update.average = dicDta4['average']
            #print("---4.1",dicDta4['average'])
            instance_update.save()

###################################################################################
#PATH para lista los conceptos con sus schemas
class EvaluationConceptSCHEMAViewSet(viewsets.ModelViewSet):
    """
        
    """
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationConceptSerializer
    queryset = EvaluationConcept.objects.all()
    action_serializers = {
        'list': EvaluationConceptListSerializerSCHEMA,
    }
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationConceptSCHEMAViewSet, self).get_serializer_class()
    def update(self, request, pk=None, project_pk=None):
        pass
    def retrieve(self, request, pk=None):
        """
            Obtener Concepto por ID
        """
        queryset = EvaluationConcept.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationConceptListSerializerSCHEMA(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        pass
## serivico crud para metadatos post crear put actualizar get traer
class EvaluationSchemaDataViewSet(viewsets.ModelViewSet):
    """
        Servicio para crear preguntas sobre la evalucaion de los OA.
        CREATE, UPDATE & DELETE Api accesible para usuario administrador.
        LIST (GET) Api accesible para totos los usuarios 
    """
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationMetadataSerializer
    queryset = EvaluationMetadata.objects.all()
    #print("-------------!",queryset )
    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar pregunta
        """
        #print("----->>>>>>",request)
        queryset = EvaluationMetadata.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationMetadataRegisterSerializer(data=request.data)
        #print("----->>>>>>",serializer)
        serializer.is_valid(raise_exception=True)
        instance.schema = serializer.validated_data['schema']
        instance.description = serializer.validated_data['description']
        instance.value_importance_schema = serializer.validated_data['value_importance_schema']
        instance.code = serializer.validated_data['code']
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        #print("entra en listar------------------")
        pass
    def destroy(self, request, pk=None):
        #print("entra en destroy------------------")
        queryset = EvaluationMetadata.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)

##########consulta evaluacion AUTOMATICA

class ListOAEvaluatedToAutomaticAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = EvaluationAutomaticEvaluationSerializer
    def get_queryset(self):
        id = self.kwargs['pk']
        var1=MetadataAutomaticEvaluation.objects.filter(
            learning_object__id=id
        ).distinct('learning_object')
        return var1






