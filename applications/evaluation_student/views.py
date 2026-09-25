"""Vistas para la evaluación estudiantil de objetos de aprendizaje.

Este módulo concentra cuatro frentes:

- entrega de la rúbrica que responde el estudiante
- captura y actualización de evaluaciones sobre un OA
- consultas públicas y privadas de resultados
- CRUD administrativo de principios, lineamientos y preguntas
"""

from copy import Error, error
from roabackend.settings import CALIFICATION_OPTIONS, YES,NO,PARTIALLY, NOT_APPLY
from applications.learning_object_metadata.serializers import LearningObjectMetadataAllSerializer, LearningObjectMetadataByStudent, ROANumberPagination
from django.db import transaction
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
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


EVALUATION_STUDENT_TAG = ['Evaluation Student']
EVALUATION_STUDENT_RESULTS_TAG = ['Evaluation Student Results']
EVALUATION_STUDENT_RUBRIC_TAG = ['Evaluation Student Rubric']
EVALUATION_STUDENT_ADMIN_TAG = ['Evaluation Student Admin']

STUDENT_EVALUATION_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador interno de la evaluacion, pregunta, principio, lineamiento u OA segun la ruta.',
)
STUDENT_EVALUATION_OA_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador del objeto de aprendizaje consultado.',
)

StudentEvaluationMessageSerializer = inline_serializer(
    name='StudentEvaluationMessage',
    fields={
        'message': serializers.CharField(),
    },
)
StudentEvaluationEmptyResponseSerializer = inline_serializer(
    name='StudentEvaluationEmptyResponse',
    fields={
        'detail': serializers.CharField(required=False),
    },
)


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_STUDENT_RUBRIC_TAG,
        summary='Listar rubrica completa para evaluacion estudiantil',
        description=(
            'Entrega la estructura que responde el estudiante. La respuesta esta organizada en tres niveles: '
            'principios, lineamientos y preguntas. Cada pregunta incluye sus textos de interpretacion para las '
            'opciones Si, No, Parcialmente y No aplica.'
        ),
        responses={
            200: PrincipleSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol estudiante.'),
        },
    )
)
class StudentQuestionAPIView(ListAPIView):
    """Entrega la rúbrica completa que el estudiante debe responder."""
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = PrincipleSerializer
    
    def get_queryset(self):
        """Lista principios en el orden histórico usado por el formulario."""
        return Principle.objects.all().order_by('id')

@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_STUDENT_TAG,
        summary='Listar evaluaciones del estudiante autenticado',
        description='Lista las evaluaciones creadas por el estudiante autenticado sobre objetos de aprendizaje.',
        responses={200: StudentEvaluationSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_STUDENT_TAG,
        summary='Obtener evaluacion estudiantil',
        description='Recupera una evaluacion concreta siempre que pertenezca al estudiante autenticado.',
        parameters=[
            STUDENT_EVALUATION_ID_PARAMETER,
        ],
        responses={
            200: StudentEvaluationSerializer,
            404: OpenApiResponse(description='Evaluacion no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=EVALUATION_STUDENT_TAG,
        summary='Registrar evaluacion estudiantil',
        description=(
            'Registra una evaluacion completa para un OA. El payload envia el id del OA, una observacion opcional '
            'y la lista de respuestas por pregunta. La vista calcula promedios por lineamiento, principio y rating final.'
        ),
        request=EvaluationStudentCreateSerializer,
        responses={
            200: StudentEvaluationSerializer,
            400: OpenApiResponse(response=StudentEvaluationMessageSerializer, description='Payload invalido u OA ya evaluado.'),
        },
    ),
    update=extend_schema(
        tags=EVALUATION_STUDENT_TAG,
        summary='Actualizar evaluacion estudiantil',
        description=(
            'Reemplaza las respuestas de una evaluacion existente, recalcula promedios por lineamiento/principio '
            'y actualiza el rating final del estudiante para ese OA.'
        ),
        request=EvaluationStudentCreateSerializer,
        parameters=[
            STUDENT_EVALUATION_ID_PARAMETER,
        ],
        responses={
            200: StudentEvaluationSerializer,
            400: StudentEvaluationMessageSerializer,
            404: OpenApiResponse(description='Evaluacion no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=EVALUATION_STUDENT_TAG,
        summary='Eliminar evaluacion estudiantil',
        description='Elimina la evaluacion del estudiante autenticado y sus respuestas asociadas.',
        parameters=[
            STUDENT_EVALUATION_ID_PARAMETER,
        ],
        responses={200: StudentEvaluationMessageSerializer},
    ),
)
class StudentEvaluationView(viewsets.ViewSet):
    """Gestiona el ciclo principal de evaluación estudiantil sobre un OA."""
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = StudentEvaluationSerializer

    def _build_question_score_map(self, results):
        """Mapea cada pregunta a su calificación numérica canónica."""
        question_scores = {}
        for result in results:
            question_id = int(result['id'])
            qualification = result['value']
            if qualification == CALIFICATION_OPTIONS['YES']:
                question_scores[question_id] = YES
            elif qualification == CALIFICATION_OPTIONS['NO']:
                question_scores[question_id] = NO
            elif qualification == CALIFICATION_OPTIONS['NOT_APPLY']:
                question_scores[question_id] = NOT_APPLY
            else:
                question_scores[question_id] = PARTIALLY
        return question_scores
    
    @transaction.atomic
    def  create(self, request, *args, **kwargs):
        """Crea una evaluación estudiantil completa para un OA."""
        serializer = EvaluationStudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(id=self.request.user.id)
        oa_is_evaluated = StudentEvaluation.objects.filter(
            learning_object__id=serializer.validated_data['learning_object'],
            student__id=user.id
            )
        if oa_is_evaluated:
            return Response({"message": "Este ya fue evaluado"},status=HTTP_400_BAD_REQUEST)

        question_scores = self._build_question_score_map(serializer.validated_data['results'])
        evaluation_questions_ = list(question_scores.keys())
        
    
        learningObjectMetadata=LearningObjectMetadata.objects.get(
            id=serializer.validated_data['learning_object']
        )
        evaluation_questions = Question.objects.filter(
             id__in=evaluation_questions_
         )

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
                                qualification=question_scores[k.id],
                                guideline_evaluations=evaluationGuideline
                            )
                            cont+=1   
                            evaluationquestions.save()
                            listEvaluationQuestions.append(evaluationquestions)
        totalguideline=0
        valor_preliminar = 0
        h = 0
        multiplicacion = 0
        ref_total_calificaciones = 0

        for a in listEvaluationGuideine:
            cont=0
            for b in listEvaluationQuestions:
                if a.id==b.guideline_evaluations.id:
                    #and b.evaluation_question_id != 1 and b.evaluation_question_id != 2 and b.evaluation_question_id != 3
                    if(b.qualification != -1):
                        #obtenemos el peso de la pregunta
                        weight_question = Question.objects.get(pk=b.evaluation_question_id)
                        # multiplicamos el peso con la calificacion de la evaluacion
                        multiplicacion = int(b.qualification) * weight_question.weight
                        totalguideline = (totalguideline + multiplicacion)

                        ref_total_calificaciones = ref_total_calificaciones + ( 2 * weight_question.weight)

                        cont+=1

            #Agreagmos la evaluacion sin el peso
            valor_preliminar = ref_total_calificaciones / cont
            valor_preliminar = valor_preliminar / 5

            h = totalguideline / cont

            a.average_guideline=(h/valor_preliminar)
            a.save()

            totalguideline = 0
            valor_preliminar = 0
            h = 0
            cont=0
            multiplicacion=0
            ref_total_calificaciones=0
        
        totalprinciple=0
        ratingOBJ=0
        cont_not_apply = 0
        cont_not_apply_principal = 0
        for i in listEvaluationPrinciple:
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
        """Lista las evaluaciones creadas por el estudiante autenticado."""
        queryset = StudentEvaluation.objects.filter(
            student__student__id=self.request.user.student.id
        )
        serializer = StudentEvaluationSerializer(queryset, many=True)
        return Response(serializer.data,status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera una evaluación concreta del estudiante autenticado."""
        queryset = StudentEvaluation.objects.filter(
        student__student__id=self.request.user.student.id,
        id=pk
        )
        get_evaluation_expert = get_object_or_404(queryset, pk=pk)
        serializer = StudentEvaluationSerializer(get_evaluation_expert)
        return Response(serializer.data, status=HTTP_200_OK)

    @transaction.atomic
    def update(self, request, pk=None, project_pk=None):
        """Actualiza respuestas, observación y rating de una evaluación existente."""
        try:

            serializer = EvaluationStudentCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = User.objects.get(id=self.request.user.id)

            question_scores = self._build_question_score_map(serializer.validated_data['results'])
            evaluation_questions_ = list(question_scores.keys())
            
        
            learningObjectMetadata=LearningObjectMetadata.objects.get(
                id=serializer.validated_data['learning_object']
            )
            evaluation_questions = Question.objects.filter(
                id__in=evaluation_questions_
            )

            queryset = StudentEvaluation.objects.filter(
                student__student__id=self.request.user.student.id
                )
            evaluation_student = get_object_or_404(queryset, pk=pk)
            evaluation_student.observation=serializer.validated_data['observation'] 
            #print("evaluation studetnt ........",evaluation_student)

            evaluationQuestionsQualifications = EvaluationQuestionQualification.objects.filter(
             guideline_evaluations__principle_gl__evaluation_student__id = pk).order_by("evaluation_question__id")

            listguideline=[]
            listquestions=[]
            for i in evaluationQuestionsQualifications:
                i.qualification=question_scores[i.evaluation_question_id]
                i.save()
                
                listquestions.append(i)

            valor_preliminar = 0
            totalnewguidelie = 0
            multiplicacion = 0
            ref_total_calificaciones = 0
            hnwe = 0
            cont2 = 0

            for i in EvaluationGuidelineQualification.objects.filter(
                principle_gl__evaluation_student__id=pk
            ):
                cont2=0
                ref_total_calificaciones=0
                for j in listquestions:

                    if i.id==j.guideline_evaluations.id:
                        #Validamos para que no se agregue las calificaciones de informacion
                        #and j.evaluation_question_id != 1 and j.evaluation_question_id != 2 and j.evaluation_question_id != 3
                        if(j.qualification != -1 ):
                            #calificaion con pero para a pregunta
                            weight_question = Question.objects.get(pk=j.evaluation_question_id)
                            # multiplicamos el peso con la calificacion de la evaluacion
                            multiplicacion = int(j.qualification) * weight_question.weight
                            totalnewguidelie = (totalnewguidelie + multiplicacion)
                            #Se usa para rellenar los calculos de la refernecia
                            ref_total_calificaciones = ref_total_calificaciones +(2 * weight_question.weight)
                            cont2+=1

               #Las cifras que se multiplican sirven para redondear la respuesta
               #ya que al aplicar la formula de la media aritmetica. Su valor maximo siempre sera 2
               #y no 5 como valor primoridial de la Evaluacion
                valor_preliminar = (ref_total_calificaciones)/(cont2)
                valor_preliminar = valor_preliminar/5

                hnwe = (totalnewguidelie)/(cont2)

                i.average_guideline = hnwe/valor_preliminar
                i.save()
                listguideline.append(i)

                valor_preliminar=0
                totalnewguidelie=0
                multiplicacion = 0
                ref_total_calificaciones=0
                hnwe=0
                cont =0


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
        """Elimina una evaluación estudiantil y sus respuestas asociadas."""
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

@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_STUDENT_RESULTS_TAG,
        summary='Listar OAs ya evaluados por el estudiante',
        description=(
            'Devuelve las evaluaciones estudiantiles del usuario autenticado, ordenadas desde la mas reciente. '
            'La respuesta incluye el OA evaluado y el detalle de la calificacion registrada.'
        ),
        responses={
            200: LearningObjectMetadataByStudent(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol estudiante.'),
        },
    )
)
class LerningObjectRatedStudent(ListAPIView):
    """Lista los OAs que el estudiante autenticado ya evaluó."""
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = LearningObjectMetadataByStudent
    pagination_class = ROANumberPagination

    def get_queryset(self):
        """Devuelve las evaluaciones del estudiante ordenadas de más recientes a más antiguas."""
        if getattr(self, 'swagger_fake_view', False):
            return StudentEvaluation.objects.none()

        query = StudentEvaluation.objects.filter(
            student__student__id=self.request.user.student.id
        ).order_by('-id')
        return query


@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_STUDENT_RESULTS_TAG,
        summary='Listar OAs pendientes de evaluar por el estudiante',
        description=(
            'Lista objetos de aprendizaje publicos que todavia no tienen evaluacion del estudiante autenticado. '
            'Sirve para alimentar el flujo de seleccion de OAs pendientes.'
        ),
        responses={
            200: LearningObjectMetadataAllSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol estudiante.'),
        },
    )
)
class LerningObjectNotRatedStudent(ListAPIView):
    """Lista OAs publicos que el estudiante actual todavía no ha evaluado."""
    permission_classes = [IsAuthenticated,IsStudentUser]
    serializer_class = LearningObjectMetadataAllSerializer
    pagination_class = ROANumberPagination
    
    def get_queryset(self):
        """Excluye los OAs ya evaluados por el estudiante autenticado."""
        if getattr(self, 'swagger_fake_view', False):
            return LearningObjectMetadata.objects.none()

        query= LearningObjectMetadata.objects.filter(
            public = True
        ).exclude(
            student_learning_objects__student__student__id=self.request.user.student.id
        ).order_by('-id')
        return query

########################################consultar evaluación

@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_STUDENT_RESULTS_TAG,
        summary='Consultar mi evaluacion estudiantil de un OA',
        description='Devuelve la evaluacion que el estudiante autenticado registro para el OA indicado.',
        parameters=[STUDENT_EVALUATION_OA_ID_PARAMETER],
        responses={
            200: EvaluationStudentList_EvaluationSerializer(many=True),
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol estudiante.'),
        },
    )
)
class ListEvaluatedToStudentRetriveAPIView(ListAPIView):
    """Lista la evaluación del estudiante autenticado para un OA concreto."""
    #permission_classes = [IsAuthenticated,(IsStudentUser | IsTeacherUser)]
    permission_classes = [IsAuthenticated,(IsStudentUser)]
    serializer_class = EvaluationStudentList_EvaluationSerializer
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StudentEvaluation.objects.none()

        id = self.kwargs['pk']
        return StudentEvaluation.objects.filter(
            student__id=self.request.user.id,
            learning_object__id=id,
        ).distinct('learning_object')

@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_STUDENT_RESULTS_TAG,
        summary='Listar evaluaciones estudiantiles publicas de un OA',
        description='Expone publicamente las evaluaciones estudiantiles asociadas al objeto de aprendizaje indicado.',
        parameters=[STUDENT_EVALUATION_OA_ID_PARAMETER],
        responses={200: EvaluationStudentList_EvaluationSerializer(many=True)},
    )
)
class ListEvaluatedToStudenPublicAPIView(ListAPIView):
    """Expone públicamente las evaluaciones estudiantiles de un OA."""
    #permission_classes = [IsAuthenticated,(IsStudentUser | IsTeacherUser)]
    permission_classes = [AllowAny]
    serializer_class = EvaluationStudentList_EvaluationSerializer
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StudentEvaluation.objects.none()

        id = self.kwargs['pk']
        return StudentEvaluation.objects.filter(
            learning_object__id=id,
        ).distinct('learning_object')

@extend_schema_view(
    get=extend_schema(
        tags=EVALUATION_STUDENT_RESULTS_TAG,
        summary='Consultar evaluacion estudiantil publica del usuario actual',
        description=(
            'Devuelve la evaluacion estudiantil del usuario actual para el OA indicado. '
            'La ruta es publica por compatibilidad, pero si no hay usuario autenticado normalmente no devolvera resultados.'
        ),
        parameters=[STUDENT_EVALUATION_OA_ID_PARAMETER],
        responses={200: EvaluationStudentList_EvaluationSerializer(many=True)},
    )
)
class ListEvaluatedStudentSinglePublicAPIView(ListAPIView):
    """Expone la evaluación del usuario actual para un OA concreto."""
    permission_classes = [AllowAny]
    serializer_class = EvaluationStudentList_EvaluationSerializer
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StudentEvaluation.objects.none()

        id = self.kwargs['pk']
        return StudentEvaluation.objects.filter(
            learning_object__id=id,
            student_id=self.request.user.id
        ).distinct('learning_object')

#######################crear preguntas del estudiante post crear put actualizar get listar
#revisar
@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Listar preguntas de evaluacion estudiantil',
        description='Lista las preguntas de la rubrica estudiantil. La lectura es publica para que el frontend pueda construir formularios.',
        responses={200: EvaluationQuestionStSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Consultar pregunta de evaluacion estudiantil',
        description='Operacion legacy sin implementacion util en la vista actual. El endpoint existe por el ViewSet, pero el metodo no devuelve detalle.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: StudentEvaluationEmptyResponseSerializer},
    ),
    create=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Crear pregunta de evaluacion estudiantil',
        description='Crea una pregunta de la rubrica estudiantil con metadata, interpretes de respuesta, peso y relevancia.',
        request=EvaluationQuestionStSerializer,
        responses={201: EvaluationQuestionStSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar pregunta de evaluacion estudiantil',
        description=(
            'Actualiza una pregunta existente. Acepta los nombres actuales del serializer y tambien aliases legacy '
            'del frontend como `schema`, `interpreter_yes`, `interpreter_no`, `interpreter_partially`, '
            '`interpreter_not_apply` y `value_importance`.'
        ),
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        request=EvaluationQuestionStRegisterSerializer,
        responses={200: StudentEvaluationMessageSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar parcialmente pregunta de evaluacion estudiantil',
        description='Operacion generada por el router. Se recomienda usar PUT porque el metodo custom espera el payload completo.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        request=EvaluationQuestionStRegisterSerializer,
        responses={200: StudentEvaluationMessageSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Eliminar pregunta de evaluacion estudiantil',
        description='Elimina una pregunta de la rubrica por identificador.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: StudentEvaluationMessageSerializer, 404: OpenApiResponse(description='Pregunta no encontrada.')},
    ),
)
class EvaluationQuestionsStudentViewSet(viewsets.ModelViewSet):
    """CRUD administrativo de preguntas de la rúbrica estudiantil."""
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationQuestionStSerializer
    queryset = Question.objects.all()

    def update(self, request, pk=None, project_pk=None):
        """Actualiza una pregunta aceptando también aliases legacy del frontend."""
        queryset = Question.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        payload = request.data.copy()
        # Compatibilidad con payload legacy del front.
        payload['metadata'] = payload.get('metadata', payload.get('schema'))
        payload['interpreter_st_yes'] = payload.get('interpreter_st_yes', payload.get('interpreter_yes'))
        payload['interpreter_st_no'] = payload.get('interpreter_st_no', payload.get('interpreter_no'))
        payload['interpreter_st_partially'] = payload.get('interpreter_st_partially', payload.get('interpreter_partially'))
        payload['interpreter_st_not_apply'] = payload.get('interpreter_st_not_apply', payload.get('interpreter_not_apply'))
        payload['value_st_importance'] = payload.get('value_st_importance', payload.get('value_importance'))

        serializer = EvaluationQuestionStRegisterSerializer(data=payload)
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
        instance.weight = serializer.validated_data['weight']
        instance.relevance = serializer.validated_data['relevance']
        ###############################################################
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """La recuperación detallada no esta implementada en este ViewSet."""
        pass

    def destroy(self, request, pk=None):
        """Elimina una pregunta de la rúbrica por identificador."""
        #print("deleteeessss",pk)
        queryset = Question.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        #print("deleteeessss",instance)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
        

#####servicio listar preguntas de sus guidelines y principios
#al pelo
@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_STUDENT_RUBRIC_TAG,
        summary='Listar lineamientos con preguntas estudiantiles',
        description='Lista lineamientos de la rubrica junto con sus preguntas. Es una lectura estructural usada por administracion y frontend.',
        responses={200: EvaluationGuidelinesListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_STUDENT_RUBRIC_TAG,
        summary='Consultar lineamiento con preguntas estudiantiles',
        description='Recupera un lineamiento concreto con sus preguntas asociadas.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationGuidelinesListSerializer, 404: OpenApiResponse(description='Lineamiento no encontrado.')},
    ),
    create=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Crear lineamiento desde vista de estructura',
        description='Operacion heredada del ModelViewSet. Para altas de lineamientos se recomienda usar `student-register-guideline`.',
        request=EvaluationGuidelinesListSerializer,
        responses={201: EvaluationGuidelinesListSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar lineamiento desde vista de estructura',
        description='Operacion legacy sin implementacion util en la vista actual.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: StudentEvaluationEmptyResponseSerializer},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar parcialmente lineamiento desde vista de estructura',
        description='Operacion legacy generada por el router; no se recomienda usarla.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: StudentEvaluationEmptyResponseSerializer},
    ),
    destroy=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Eliminar lineamiento desde vista de estructura',
        description='Operacion legacy sin implementacion util en la vista actual.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: StudentEvaluationEmptyResponseSerializer},
    ),
)
class EvaluationPrincipleGuidelienViewSet(viewsets.ModelViewSet):
    """Lista lineamientos junto con sus preguntas para consumo administrativo."""
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
        """Recupera un lineamiento con sus preguntas asociadas."""
        #Principle antes
        queryset = Guideline.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        #EvaluationPrincipleListSerializer antes
        serializer = EvaluationGuidelinesListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        pass


####################################################servicio para crear un principio

@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_STUDENT_RUBRIC_TAG,
        summary='Listar principios de evaluacion estudiantil',
        description='Lista principios de la rubrica con sus lineamientos y preguntas para vistas administrativas.',
        responses={200: EvaluationPrincipleRegListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_STUDENT_RUBRIC_TAG,
        summary='Consultar principio de evaluacion estudiantil',
        description='Recupera un principio con su estructura completa de lineamientos y preguntas.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationPrincipleRegListSerializer, 404: OpenApiResponse(description='Principio no encontrado.')},
    ),
    create=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Crear principio de evaluacion estudiantil',
        description='Crea un principio general de la rubrica estudiantil.',
        request=EvaluationPrincipleRegSerializer,
        responses={201: EvaluationPrincipleRegSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar principio de evaluacion estudiantil',
        description='Actualiza el texto del principio indicado.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        request=EvaluationPrincipleRegSerializer,
        responses={200: StudentEvaluationMessageSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar parcialmente principio de evaluacion estudiantil',
        description='Operacion generada por router. Se recomienda usar PUT porque la vista custom solo actualiza el campo `principle`.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        request=EvaluationPrincipleRegSerializer,
        responses={200: StudentEvaluationMessageSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Eliminar principio de evaluacion estudiantil',
        description='Elimina un principio de la rubrica por identificador.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: StudentEvaluationMessageSerializer, 404: OpenApiResponse(description='Principio no encontrado.')},
    ),
)
class EvaluationPrincipleRegisterViewSet(viewsets.ModelViewSet):
    """CRUD administrativo de principios de la rúbrica estudiantil."""
    
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
        """Actualiza el texto de un principio existente."""
        queryset = Principle.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.principle = request.data['principle']
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """Recupera un principio con sus lineamientos y preguntas asociadas."""
        queryset = Principle.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer =  EvaluationPrincipleRegListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """Elimina un principio de evaluación por identificador."""
        queryset = Principle.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
    
#########################CRUD DE LOS GUIDELINE

@extend_schema_view(
    list=extend_schema(
        tags=EVALUATION_STUDENT_RUBRIC_TAG,
        summary='Listar lineamientos de evaluacion estudiantil',
        description='Lista lineamientos registrados en la rubrica estudiantil.',
        responses={200: EvaluationQuestionGuidelinesRegSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=EVALUATION_STUDENT_RUBRIC_TAG,
        summary='Consultar lineamiento de evaluacion estudiantil',
        description='Recupera un lineamiento concreto de la rubrica.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: EvaluationQuestionGuidelinesRegSerializer, 404: OpenApiResponse(description='Lineamiento no encontrado.')},
    ),
    create=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Crear lineamiento de evaluacion estudiantil',
        description='Crea un lineamiento asociado a un principio de la rubrica estudiantil.',
        request=EvaluationQuestionGuidelinesRegSerializer,
        responses={201: EvaluationQuestionGuidelinesRegSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar lineamiento de evaluacion estudiantil',
        description='Actualiza el texto de un lineamiento existente. El flujo valida unicidad del nombre del lineamiento.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        request=EvaluationGuidelineValidRegisterSerializer,
        responses={200: StudentEvaluationMessageSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Actualizar parcialmente lineamiento de evaluacion estudiantil',
        description='Operacion generada por router. Se recomienda usar PUT porque el metodo custom espera el campo `guideline`.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        request=EvaluationGuidelineValidRegisterSerializer,
        responses={200: StudentEvaluationMessageSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=EVALUATION_STUDENT_ADMIN_TAG,
        summary='Eliminar lineamiento de evaluacion estudiantil',
        description='Elimina un lineamiento de la rubrica por identificador.',
        parameters=[STUDENT_EVALUATION_ID_PARAMETER],
        responses={200: StudentEvaluationMessageSerializer, 404: OpenApiResponse(description='Lineamiento no encontrado.')},
    ),
)
class EvaluationGuidelineRegisterViewSet(viewsets.ModelViewSet):
    """CRUD administrativo de lineamientos de la rúbrica estudiantil."""
    def get_permissions(self):
        if(self.action=='list'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EvaluationQuestionGuidelinesRegSerializer
    queryset = Guideline.objects.all()

    def update(self, request, pk=None, project_pk=None):
        """Actualiza el texto de un lineamiento existente."""
        #print("entro en el original")
        queryset = Guideline.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationGuidelineValidRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.guideline = serializer.validated_data['guideline']
        instance.save()
        return Response({"message": "success"},status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """Recupera un lineamiento por identificador."""
        queryset = Guideline.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = EvaluationQuestionGuidelinesRegSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """Elimina un lineamiento de la rúbrica."""
        queryset = Guideline.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
    
