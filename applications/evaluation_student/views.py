from copy import Error, error
from roabackend.settings import CALIFICATION_OPTIONS, YES,NO,PARTIALLY, NOT_APPLY
from applications.learning_object_metadata.serializers import LearningObjectMetadataAllSerializer, LearningObjectMetadataByStudent, ROANumberPagination
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from applications.user.models import User
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.evaluation_student.serializers import (
    EvaluationGuidelineValidRegisterSerializer,
    EvaluationGuidelinesListSerializer,
    EvaluationPrincipleListSerializer,
    EvaluationPrincipleRegListSerializer,
    EvaluationPrincipleRegSerializer,
    EvaluationQuestionGuidelinesRegSerializer,
    EvaluationQuestionStRegisterSerializer,
    EvaluationQuestionStSerializer,
    EvaluationStudentCreateSerializer,
    EvaluationStudentList_EvaluationSerializer,
    Evaluation_Student_Serializer, 
    PrincipleSerializer,
    StudentEvaluationSerializer
)
from applications.evaluation_student.models import (
    EvaluationGuidelineQualification,
    EvaluationPrincipleQualification,
    EvaluationQuestionQualification,
    Guideline,
    Principle, 
    Question, 
    StudentEvaluation
)
from applications.user.mixins import IsAdministratorUser, IsStudentUser, IsTeacherUser
# Create your views here.
class StudentQuestionAPIView(ListAPIView):
    """
        Servicio para listar la evaluación del estudiante
    """
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = PrincipleSerializer
    def get_queryset(self):
        return Principle.objects.all().order_by('id')

class StudentEvaluationView(viewsets.ViewSet):
    """
        Servicio para crear una evaluación por el estudiante
    """
    permission_classes = [IsAuthenticated,IsStudentUser]
    def  create(self, request, *args, **kwargs):
        serializer = EvaluationStudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(id=self.request.user.id)
        oa_is_evaluated = StudentEvaluation.objects.filter(
            learning_object__id=serializer.validated_data['learning_object'],
            student__id=user.id
            )
        if oa_is_evaluated:
            return Response({"message": "Este ya fue evaluado"},status=HTTP_400_BAD_REQUEST)

        evaluation_questions_ =  []
        qualifications =  []
        for result in serializer.validated_data['results']:
            evaluation_questions_.append(result['id'])
            qualifications.append(result['value'])
        
    
        learningObjectMetadata=LearningObjectMetadata.objects.get(
            id=serializer.validated_data['learning_object']
        )
        evaluation_questions = Question.objects.filter(
             id__in=evaluation_questions_
         )

        scores = []
        for qualification in qualifications:
            if(qualification== CALIFICATION_OPTIONS['YES']):
                scores.append(YES)
            elif(qualification==CALIFICATION_OPTIONS['NO']):
                scores.append(NO)
            elif (qualification == CALIFICATION_OPTIONS['NOT_APPLY']):
                scores.append(NOT_APPLY)
            else:
                scores.append(PARTIALLY)
        #print("----------------",scores)

        evaluationStudent= StudentEvaluation.objects.create(
            learning_object=learningObjectMetadata,
            observation=serializer.validated_data['observation'],
            rating=0.0,
            student=user
        ) 
        evaluationStudent.save()
        #############################################################
        listEvaluationPrinciple=[] 
        listEvaluationGuideine=[]
        listEvaluationQuestions=[]
        for i in Principle.objects.all():
            evaluationPrinciple=EvaluationPrincipleQualification.objects.create(
                evaluation_principle=i,
                average_principle=0.0,
                evaluation_student=evaluationStudent
            )
            evaluationPrinciple.save()
            listEvaluationPrinciple.append(evaluationPrinciple)
            for j in Guideline.objects.all():
                if j.principle.id==i.id:
                    evaluationGuideline=EvaluationGuidelineQualification.objects.create(
                        guideline_pr=j,
                        average_guideline=0.0,
                        principle_gl=evaluationPrinciple
                    )
                    evaluationGuideline.save()
                    listEvaluationGuideine.append(evaluationGuideline)
                    cont=0
                    for k in Question.objects.all():
                        if k.guideline.id==evaluationGuideline.guideline_pr.id:
                            evaluationquestions=EvaluationQuestionQualification.objects.create(
                                evaluation_question=k,
                                qualification=scores[cont],
                                guideline_evaluations=evaluationGuideline
                            )
                            cont+=1   
                            evaluationquestions.save()
                            listEvaluationQuestions.append(evaluationquestions)
        totalguideline=0
        for a in listEvaluationGuideine:
            cont=0
            for b in listEvaluationQuestions:
                if a.id==b.guideline_evaluations.id:
                    if(b.qualification != -1 and b.evaluation_question_id != 1 and b.evaluation_question_id != 2 and b.evaluation_question_id != 3):
                        #obtenemos el peso de la pregunta
                        weight_question = Question.objects.get(pk=b.evaluation_question_id)
                        # multiplicamos el peso con la calificacion de la evaluacion
                        multiplicacion = b.qualification * weight_question.weight
                        totalguideline = (totalguideline + multiplicacion)
                        cont+=1

            #Agreagmos la evaluacion sin el peso
            h = (totalguideline) / (cont)
            a.average_guideline=(h/2.4)
            a.save()

            totalguideline=0
        
        totalprinciple=0
        ratingOBJ=0
        cont_not_apply = 0
        cont_not_apply_principal = 0
        for i, qualification in zip(listEvaluationPrinciple, scores):
            contg=0
            for j in listEvaluationGuideine:
                if i.id==j.principle_gl.id:
                    #if (qualification != -1):
                        totalprinciple+=j.average_guideline
                        contg+=1
                    #else:
                     #   cont_not_apply_principal += 1


            i.average_principle=totalprinciple/(contg)
            i.save()

            #if (qualification != -1):
            ratingOBJ += i.average_principle
            #else:
             #   cont_not_apply += 1

            totalprinciple=0
            contg=0

        evaluationStudent.rating=ratingOBJ/(len(Principle.objects.all()))
        evaluationStudent.save()  
        serializer = StudentEvaluationSerializer(evaluationStudent)
        #serializer = Evaluation_Student_Serializer(evaluationStudent)
        return Response(serializer.data, status=HTTP_200_OK)
        ############################################################3
    def list(self, request):
        """
            Servicio para listar calificacion del estudiante
        """
        queryset = StudentEvaluation.objects.filter(
            student__student__id=self.request.user.student.id
        )
        serializer = StudentEvaluationSerializer(queryset, many=True)
        return Response(serializer.data,status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para obtener una calificacion del estudiante
        """
        queryset = StudentEvaluation.objects.filter(
        student__student__id=self.request.user.student.id,
        id=pk
        )
        get_evaluation_expert = get_object_or_404(queryset, pk=pk)
        serializer = StudentEvaluationSerializer(get_evaluation_expert)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actuaizar una evalución
        """
        try:

            serializer = EvaluationStudentCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = User.objects.get(id=self.request.user.id)

            evaluation_questions_ =  []
            qualifications =  []
            for result in serializer.validated_data['results']:
                evaluation_questions_.append(result['id'])
                qualifications.append(result['value'])
            
        
            learningObjectMetadata=LearningObjectMetadata.objects.get(
                id=serializer.validated_data['learning_object']
            )
            evaluation_questions = Question.objects.filter(
                id__in=evaluation_questions_
            )

            scores = []
            for qualification in qualifications:
                if(qualification== CALIFICATION_OPTIONS['YES']):
                    scores.append(YES)
                elif(qualification==CALIFICATION_OPTIONS['NO']):
                    scores.append(NO)
                elif (qualification == CALIFICATION_OPTIONS['NOT_APPLY']):
                    scores.append(NOT_APPLY)
                else:
                    scores.append(PARTIALLY)

            queryset = StudentEvaluation.objects.filter(
                student__student__id=self.request.user.student.id
                )
            evaluation_student = get_object_or_404(queryset, pk=pk)
            evaluation_student.observation=serializer.validated_data['observation'] 
            #print("evaluation studetnt ........",evaluation_student)


            evaluationQuestionsQualifications = EvaluationQuestionQualification.objects.filter(
             guideline_evaluations__principle_gl__evaluation_student__id = pk).order_by("evaluation_question__id")

            
            
            #print(",,,,,,,,,,,,,,,,,,,,,,,,,",scores)
            listguideline=[]
            cont=0
            listquestions=[]
            for i in evaluationQuestionsQualifications:
                i.qualification=scores[cont]
                i.save()
                cont+=1
                
                listquestions.append(i)
            totalnewguidelie=0
            
            for i in EvaluationGuidelineQualification.objects.filter(
                principle_gl__evaluation_student__id=pk
            ):
                cont2=0
                for j in listquestions:

                    if i.id==j.guideline_evaluations.id:
                        #Validamos para que no se agregue las calificaciones de informacion
                        if(j.qualification != -1 and b.evaluation_question_id != 1 and b.evaluation_question_id != 2 and b.evaluation_question_id != 3):
                            #calificaion con pero para a pregunta
                            weight_question = Question.objects.get(pk=j.evaluation_question_id)
                            # multiplicamos el peso con la calificacion de la evaluacion
                            multiplicacion = j.qualification * weight_question.weight
                            totalnewguidelie = (totalnewguidelie + multiplicacion)
                            cont2+=1
                try:
                   #Las cifras que se multiplican sirven para redondear la respuesta
                   #ya que al aplicar la formula de la media aritmetica. Su valor maximo siempre sera 2
                   #y no 5 como valor primoridial de la Evaluacion
                    hnwe = (totalnewguidelie)/(cont2)
                    #2.4 Cifra para redondear la calificacion a 5
                    i.average_guideline = (hnwe/2.4)
                    i.save()
                    listguideline.append(i)
                    totalnewguidelie=0
                except:
                    hnwe=0

            totalprinciple_new=0
            totalrating_new=0
            cont_not_apply = 0
            for i in EvaluationPrincipleQualification.objects.filter(
                evaluation_student__id=pk
            ):
                cont3=0
                for j in listguideline:
                    if i.id==j.principle_gl.id:
                        #if (qualification != -1):
                        totalprinciple_new+=j.average_guideline
                        cont3+=1
                        #else:
                         #   cont_not_apply += 1
                try:

                    i.average_principle=totalprinciple_new/cont3

                except:
                    pass

                i.save()
                totalrating_new+=i.average_principle
                totalprinciple_new=0

            evaluation_student.rating=totalrating_new/(len(Principle.objects.all()))

            evaluation_student.save() 
            serializer = StudentEvaluationSerializer(evaluation_student)            
        except Error as e:
            #print("error--------------",e)
            return Response({"message": "an error occurred"} ,status=HTTP_400_BAD_REQUEST)
        return Response(serializer.data,status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """
            Servicio para eliminat una evaluación
        """
        evaluationQuestionQualifications = EvaluationQuestionQualification.objects.filter(
            student_evaluation__student__id = pk
        )
        for evaluationQuestionsQualification in evaluationQuestionQualifications:
            evaluationQuestionsQualification.delete()

        queryset = StudentEvaluation.objects.filter(
            student__student__id=self.request.user.student.id,
        )
        evaluation_expert = get_object_or_404(queryset, pk=pk)
        evaluation_expert.delete()
        return Response({"message": "success"},status=HTTP_200_OK) 

class LerningObjectRatedStudent(ListAPIView):
    """
        Servicio para listar OAs evaluados por el estudiante
    """
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = LearningObjectMetadataByStudent
    pagination_class = ROANumberPagination
    def get_queryset(self):
        query = StudentEvaluation.objects.filter(
            student__student__id=self.request.user.student.id
        ).order_by('-id')
        return query


class LerningObjectNotRatedStudent(ListAPIView):
    """
        Servicio para listar OAs no evaludos por el estudiante
    """
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    def get_queryset(self):
        query= LearningObjectMetadata.objects.filter(
            public = True
        ).exclude(
            student_learning_objects__student__student__id=self.request.user.student.id
        ).order_by('-id')
        return query

########################################consultar evaluacion

class ListEvaluatedToStudentRetriveAPIView(ListAPIView):
    """
        Listar resultado de la evaluación realizado por el experto por id del OA.
        El servicio requiere de la autenticación como experto.
    """
    #permission_classes = [IsAuthenticated,(IsStudentUser | IsTeacherUser)]
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = EvaluationStudentList_EvaluationSerializer
    def get_queryset(self):
        id = self.kwargs['pk']
        return StudentEvaluation.objects.filter(
            student__id=self.request.user.id,
            learning_object__id=id,
        ).distinct('learning_object')

class ListEvaluatedToStudenPublicAPIView(ListAPIView):
    """
        Listar resultado de la evaluación realizado por el experto por id del OA.
        El servicio requiere de la autenticación como experto.
    """
    #permission_classes = [IsAuthenticated,(IsStudentUser | IsTeacherUser)]
    permission_classes = [AllowAny]
    serializer_class = EvaluationStudentList_EvaluationSerializer
    def get_queryset(self):
        id = self.kwargs['pk']
        return StudentEvaluation.objects.filter(
            learning_object__id=id,
        ).distinct('learning_object')



#######################crear preguntas del estudiante post crear put actualizar get listar
#revisar 
class EvaluationQuestionsStudentViewSet(viewsets.ModelViewSet):
    """
        Servicio para crear preguntas sobre la evalucaion de los OA.
        CREATE, UPDATE & DELETE Estudiante
    """
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationQuestionStSerializer
    queryset = Question.objects.all()
    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar pregunta
        """
        print("entro en el original")
        queryset = Question.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationQuestionStRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.question = serializer.validated_data['question']
        instance.description = serializer.validated_data['description']
        instance.metadata = serializer.validated_data['metadata']
        ##############################################################
        instance.interpreter_st_yes = serializer.validated_data['interpreter_st_yes']
        instance.interpreter_st_no = serializer.validated_data['interpreter_st_no']
        instance.interpreter_st_partially = serializer.validated_data['interpreter_st_partially']
        instance.interpreter_st_not_apply = serializer.validated_data['interpreter_st_not_apply']
        instance.value_st_importance = serializer.validated_data['value_st_importance']
        ###############################################################
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Obtener pregunta por ID
        """
        pass
    def destroy(self, request, pk=None):
        """
            Eliminar pregunta
        """
        #print("deleteeessss",pk)
        queryset = Question.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        #print("deleteeessss",instance)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
        

#####servicio listar preguntas de sus guidelines y principios
#al pelo
class EvaluationPrincipleGuidelienViewSet(viewsets.ModelViewSet):
    """
       
    """
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
        #EvaluationPrincipleListSerializer antes
    serializer_class = EvaluationGuidelinesListSerializer
    #Principle antes
    queryset = Guideline.objects.all()
    action_serializers = {
        'list': EvaluationGuidelinesListSerializer,
    }
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationPrincipleGuidelienViewSet, self).get_serializer_class()
    def update(self, request, pk=None, project_pk=None):
        pass
    def retrieve(self, request, pk=None):
        """
            Obtener Concepto por ID
        """
        #Principle antes
        queryset = Guideline.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        #EvaluationPrincipleListSerializer antes
        serializer = EvaluationGuidelinesListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        pass


####################################################servicio para crear un principio

class EvaluationPrincipleRegisterViewSet(viewsets.ModelViewSet):
    """
        Servicio crear conceptos de Objeto de Aprendizaje.
        CREATE, UPDATE & DELETE 
    """
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationPrincipleRegSerializer
    queryset = Principle.objects.all()
    action_serializers = {
        'list': EvaluationPrincipleRegListSerializer,
    }
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EvaluationPrincipleRegisterViewSet, self).get_serializer_class()
    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar concepto
        """
        queryset = Principle.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.concept = request.data['principle']
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Obtener Concepto por ID
        """
        queryset = Principle.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer =  EvaluationPrincipleRegListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        """
            Eliminar el concepto de evaluación
        """
        queryset = Principle.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
    
#########################CRUD DE LOS GUIDELINE

class EvaluationGuidelineRegisterViewSet(viewsets.ModelViewSet):
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
    serializer_class = EvaluationQuestionGuidelinesRegSerializer
    queryset = Guideline.objects.all()
    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar 
        """
        #print("entro en el original")
        queryset = Guideline.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationGuidelineValidRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.guideline = serializer.validated_data['guideline']
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Obtener pregunta por ID
        """
        queryset = Guideline.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationQuestionGuidelinesRegSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        """
            Eliminar pregunta
        """
        queryset = Guideline.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
    