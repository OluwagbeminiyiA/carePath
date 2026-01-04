from asgiref.sync import async_to_sync
from django.db import transaction
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Queue, Hospital, Patient
from .serializers import HospitalSerializer, QueueSerializer, PatientDetailSerializer, JoinQueueSerializer, \
    QueueUpdateSerializer, DrugCheckSerializer, DrugCheckResponseSerializer, DrugAuthenticationSerializer, \
    DrugAuthenticationResponseSerializer
from .services import DrugValidityService, DrugAuthenticationService
from channels.layers import get_channel_layer


# Create your views here.
def getEstimatedTime(queue_number: int):
    pass


class HospitalListView(APIView):
    @method_decorator(cache_page(60 * 60 * 2))
    @extend_schema(
        responses={200: HospitalSerializer(many=True)},
        methods=['GET'],
        description="Retrieve a list of all hospitals."
    )
    def get(self, request):
        hospitals = Hospital.objects.all()
        serializer = HospitalSerializer(hospitals, many=True, context={'request': request})
        return Response(serializer.data)


class HospitalDetailView(APIView):
    @method_decorator(cache_page(60 * 60 * 2))
    @extend_schema(
        responses={200: HospitalSerializer},
        methods=['GET'],
        description="Retrieve details of a specific hospital by ID."
    )
    def get(self, request, pk):
        hospital = Hospital.objects.get(id=pk)
        serializer = HospitalSerializer(hospital, context={'request': request})
        return Response(serializer.data)


class HospitalCreateView(APIView):
    @extend_schema(
        request=HospitalSerializer,
        responses={201: HospitalSerializer},
        methods=['POST'],
        description="Create a new hospital."
    )
    def post(self, request):
        email = request.data.get('email')
        if email and Hospital.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = HospitalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientListView(APIView):
    @method_decorator(cache_page(60 * 60 * 2))
    @extend_schema(
        responses={200: PatientDetailSerializer(many=True)},
        methods=['GET'],
        description="Retrieve a list of all patients."
    )
    def get(self, request):
        patients = Patient.objects.all()
        serializer = PatientDetailSerializer(patients, many=True)
        return Response(serializer.data)


class PatientDetailView(APIView):
    @method_decorator(cache_page(60 * 60 * 2))
    @extend_schema(
        responses={200: PatientDetailSerializer},
        methods=['GET'],
        description="Retrieve details of a specific patient by ID."
    )
    def get(self, request, pk):
        patient = Patient.objects.get(id=pk)
        serializer = PatientDetailSerializer(patient, context={'request': request})
        return Response(serializer.data)


class PatientCreateView(APIView):
    @extend_schema(
        request=PatientDetailSerializer,
        responses={201: PatientDetailSerializer},
        methods=['POST'],
        description="Create a new patient."
    )
    def post(self, request):
        serializer = PatientDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors.get('status'))
        return Response({'Error Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class QueueListView(APIView):
    @method_decorator(cache_page(60 * 60 * 2))
    @extend_schema(
        responses={200: QueueSerializer(many=True)},
        methods=['GET'],
        description="Retrieve a list of all queues."
    )
    def get(self, request):
        queues = Queue.objects.all()
        serializer = QueueSerializer(queues, many=True)
        return Response(serializer.data)


class QueueDetailForPatient(APIView):
    @method_decorator(cache_page(60 * 60 * 2))
    @extend_schema(
        responses={200: QueueSerializer},
        methods=['GET'],
        description="Retrieve queue details for a specific patient."
    )
    def get(self, request, patient_id):
        queue = get_object_or_404(Queue, patient_id=patient_id)
        serializer = QueueSerializer(queue, context={'request': request})
        return Response(serializer.data)


class JoinQueueView(APIView):
    @extend_schema(
        request=JoinQueueSerializer,
        responses={201: JoinQueueSerializer},
        methods=['POST'],
        description="Join a hospital queue."
    )
    def post(self, request, hospital_id):
        # Auto-generate queue_number
        hospital = hospital_id
        patient = request.data['patient']

        if Queue.objects.filter(patient=patient).exists():
            return Response({'error': 'Patient already on Queue'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            last_queue = Queue.objects.select_for_update().filter(hospital_id=hospital).order_by('queue_number').last()
            new_queue_number = (last_queue.queue_number + 1) if last_queue else 1

            data = request.data
            data['hospital'] = hospital
            data['queue_number'] = new_queue_number

            data['queue_status'] = 'WAITING'

            serializer = JoinQueueSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                current_queue_count = Queue.objects.filter(hospital_id=hospital, queue_status="WAITING").count()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"hospital_{hospital}",
                    {
                        "type": "queue_update",
                        "count": current_queue_count,
                    }
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors.items())
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QueueUpdateView(APIView):
    @extend_schema(
        request=QueueUpdateSerializer,
        responses={200: QueueUpdateSerializer},
        description="Updates patient status and automatically decrements the queue position of all following patients.",
        summary="Complete patient visit and shift queue"
    )
    def put(self, request, patient_id):
        with transaction.atomic():
            queue = Queue.objects.get(patient=patient_id)

            serializer = QueueUpdateSerializer(queue, data=request.data)
            if serializer.is_valid():
                serializer.save()
                current_patient_status = Queue.objects.filter(patient=patient_id).last().queue_status
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"patient_{patient_id}",
                    {
                        "type": "queue_status_update",
                        "status": current_patient_status,
                    }
                )
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DrugValidityCheckView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'drug_image': {
                        'type': 'string',
                        'format': 'binary'
                    },
                    'symptoms': {
                        'type': 'string'
                    }
                },
                'required': ['drug_image', 'symptoms']
            }
        },
        responses={200: DrugCheckResponseSerializer},
        description="Analyze if a drug (uploaded as image) is suitable for the given symptoms using AI. Requires multipart/form-data.",
        summary="Check drug validity from image"
    )
    def post(self, request):
        serializer = DrugCheckSerializer(data=request.data)
        if serializer.is_valid():
            service = DrugValidityService()
            result = service.analyze(
                drug_image=serializer.validated_data['drug_image'],
                symptoms=serializer.validated_data['symptoms']
            )
            
            if "error" in result:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DrugAuthenticationCheckView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'drug_image': {
                        'type': 'string',
                        'format': 'binary'
                    }
                },
                'required': ['drug_image']
            }
        },
        responses={200: DrugAuthenticationResponseSerializer},
        description="Analyze if a drug (uploaded as image) is authentic or fake using AI. Requires multipart/form-data.",
        summary="Check drug authenticity from image"
    )
    def post(self, request):
        serializer = DrugAuthenticationSerializer(data=request.data)
        if serializer.is_valid():
            service = DrugAuthenticationService()
            result = service.authenticate(
                drug_image=serializer.validated_data['drug_image']
            )
            
            if "error" in result:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
