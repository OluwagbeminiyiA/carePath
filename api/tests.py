import datetime
import json
from io import BytesIO
from unittest.mock import patch, MagicMock

from PIL import Image
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from carePath.asgi import application
from .models import Hospital, Queue, Patient


# Create your tests here.


class TestApi(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.hospital = Hospital.objects.create(
            name="Hospital 1",
            address="123 Main Street",
            city="New York",
            state="New York",
            email="<EMAIL>",
            phone="0123456789",
            longitude=3.339844,
            latitude=6.555475,
        )

        self.hospital2 = Hospital.objects.create(
            name="Hospital 2",
            address="123 Main Street",
            city="New York",
            state="New York",
            email="hospital2@email.com",
            phone="012345",
            longitude=3.339844,
            latitude=6.555475,
        )

        self.patient = Patient.objects.create(
            first_name="Patient 1",
            last_name="<NAME>",
            email="<EMAIL>",
            phone="0123456789",
            address="123 Main Street",
            date_of_birth=datetime.date(1999, 12, 25),
            status="RETURNING",
            hospital=self.hospital,
        )

        queue_number = Queue.objects.create(
            patient=self.patient,
            hospital=self.hospital,
            queue_number=1,
            queue_status='WAITING',

        )

        self.patient2 = Patient.objects.create(
            first_name="Patient 2",
            last_name="<NAME>",
            email="email2@email.com",
            phone="0123456789",
            address="123 Main Street",
            date_of_birth=datetime.date(1999, 12, 25),
            status="RETURNING",
            hospital=self.hospital,
        )
        self.patient3 = Patient.objects.create(
            first_name="Patient 2",
            last_name="<NAME>",
            email="email3@email.com",
            phone="01234567",
            address="123 Main Street",
            date_of_birth=datetime.date(1999, 12, 25),
            status="RETURNING",
            hospital=self.hospital,
        )

    def testGetHospitals(self):
        response = self.client.get('/api/hospitals/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Hospital 1')
        self.assertEqual(response.data[0]['address'], '123 Main Street')
        self.assertEqual(response.data[0]['city'], 'New York')

    def testGetHospital(self):
        response = self.client.get('/api/hospital/1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Hospital 1')
        self.assertEqual(response.data['address'], '123 Main Street')

    def testCreateHospital(self):
        response = self.client.post('/api/hospital/create/',
                                    {
                                        'name': 'Hospital 1',
                                        'address': '123 Main Street',
                                        'city': 'New York',
                                        'state': 'New York',
                                        'email': 'email@email.com',
                                        'phone': '0123456789',
                                        'longitude': 3.339844,
                                        'latitude': 6.555475
                                    }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testGetPatients(self):
        response = self.client.get('/api/patients/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['first_name'], 'Patient 1')
        self.assertEqual(response.data[0]['address'], '123 Main Street')

    def testGetPatient(self):
        response = self.client.get('/api/patient/1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Patient 1')

    def testCreatePatient(self):
        response = self.client.post('/api/patient/create/',
                                    {
                                        'first_name': 'Patient 1',
                                        'last_name': '<NAME>',
                                        'address': '123 Main Street',
                                        'email': 'email@email.com',
                                        'phone': '01234567',
                                        'date_of_birth': datetime.date(1998, 12, 25),
                                        'status': 'RETURNING',
                                        'hospital': self.hospital.id
                                    }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Patient 1')
        self.assertEqual(response.data['last_name'], '<NAME>')

    def testGetQueues(self):
        response = self.client.get('/api/queue/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['queue_number'], 1)
        self.assertEqual(response.data[0]['queue_status'], 'WAITING')

    def testGetQueueNumberForPatient(self):
        response = self.client.get('/api/queue/find/1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['queue_number'], 1)
        self.assertEqual(response.data['queue_status'], 'WAITING')

    def testJoinQueue(self):
        response = self.client.post('/api/queue/join/1/',
                                    {
                                        'patient': self.patient2.id,
                                    }, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['hospital'], self.hospital.id)
        self.assertEqual(response.data['queue_number'], 2)
        self.assertEqual(response.data['queue_status'], 'WAITING')
        self.assertEqual(response.data['patient'], self.patient2.pk)

    def testUpdateQueue(self):
        response = self.client.put('/api/queue/update/1/',
                                   {
                                       'queue_status': 'CALLED',
                                   }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['queue_status'], 'CALLED')
        self.assertEqual(response.data['patient'], self.patient.pk)
        self.assertEqual(response.data['hospital'], self.hospital.id)
        self.assertEqual(Queue.objects.get(patient=1).queue_number, 0)

    def testSameQueueNumberWithDifferentHospital(self):
        response = self.client.post(
            f'/api/queue/join/{self.hospital2.id}/',
            {
                'patient': self.patient3.id,
                'queue_status': 'WAITING'
            }, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['queue_number'], 1)
        self.assertEqual(response.data['queue_status'], 'WAITING')
        self.assertEqual(response.data['patient'], self.patient3.pk)

    def testPatientWithMultipleQueueNumbers(self):
        response = self.client.post(f"/api/queue/join/{self.hospital.id}/",
                                    {
                                        'patient': self.patient.id,
                                        'queue_status': 'WAITING',
                                    }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Patient already on Queue')

    def testPatientWithMultipleHospitalQueueNumbers(self):
        response = self.client.post(f"/api/queue/join/{self.hospital2.id}/",
                                    {
                                        'patient': self.patient.id,
                                        'queue_status': 'WAITING',
                                    }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Patient already on Queue')


class TestDrugValidity(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a dummy image
        self.image_file = BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(self.image_file, 'jpeg')
        self.image_file.seek(0)

        self.uploaded_image = SimpleUploadedFile(
            name='test_drug.jpg',
            content=self.image_file.read(),
            content_type='image/jpeg'
        )

    @override_settings(GEMINI_API_KEY='fake-key')
    def test_drug_validity_check_success(self):
        # Mock the google.genai module
        mock_genai = MagicMock()
        mock_client_class = mock_genai.Client
        mock_client_instance = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "drug_identified": "Ibuprofen",
            "is_suitable": True,
            "confidence": 0.95,
            "explanation": "Ibuprofen is commonly used for headaches."
        })
        mock_client_instance.models.generate_content.return_value = mock_response

        with patch.dict('sys.modules', {'google.genai': mock_genai}):
            data = {
                'drug_image': self.uploaded_image,
                'symptoms': 'Headache'
            }

            response = self.client.post('/api/drug/check/', data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['drug_identified'], 'Ibuprofen')
        self.assertTrue(response.data['is_suitable'])
        self.assertEqual(response.data['confidence'], 0.95)

    @override_settings(GEMINI_API_KEY='fake-key')
    def test_drug_validity_check_api_error(self):
        # Mock the google.genai module
        mock_genai = MagicMock()
        mock_client_class = mock_genai.Client
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.models.generate_content.side_effect = Exception("API Error")

        with patch.dict('sys.modules', {'google.genai': mock_genai}):
            # Reset file pointer for reuse
            self.image_file.seek(0)
            uploaded_image = SimpleUploadedFile(
                name='test_drug.jpg',
                content=self.image_file.read(),
                content_type='image/jpeg'
            )

            data = {
                'drug_image': uploaded_image,
                'symptoms': 'Headache'
            }

            response = self.client.post('/api/drug/check/', data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class TestDrugAuthentication(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a dummy image
        self.image_file = BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(self.image_file, 'jpeg')
        self.image_file.seek(0)

        self.uploaded_image = SimpleUploadedFile(
            name='test_auth_drug.jpg',
            content=self.image_file.read(),
            content_type='image/jpeg'
        )

    @override_settings(GEMINI_API_KEY='fake-key')
    def test_drug_authentication_success(self):
        # Mock the google.genai module
        mock_genai = MagicMock()
        mock_client_class = mock_genai.Client
        mock_client_instance = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "drug_identified": "Panadol",
            "is_authentic": True,
            "confidence": 0.98,
            "explanation": "Packaging looks correct with proper holographic seal."
        })
        mock_client_instance.models.generate_content.return_value = mock_response

        with patch.dict('sys.modules', {'google.genai': mock_genai}):
            data = {
                'drug_image': self.uploaded_image
            }

            response = self.client.post('/api/drug/authenticate/', data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['drug_identified'], 'Panadol')
        self.assertTrue(response.data['is_authentic'])
        self.assertEqual(response.data['confidence'], 0.98)

    @override_settings(GEMINI_API_KEY='fake-key')
    def test_drug_authentication_api_error(self):
        # Mock the google.genai module
        mock_genai = MagicMock()
        mock_client_class = mock_genai.Client
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.models.generate_content.side_effect = Exception("API Error")

        with patch.dict('sys.modules', {'google.genai': mock_genai}):
            # Reset file pointer for reuse
            self.image_file.seek(0)
            uploaded_image = SimpleUploadedFile(
                name='test_auth_drug.jpg',
                content=self.image_file.read(),
                content_type='image/jpeg'
            )

            data = {
                'drug_image': uploaded_image
            }

            response = self.client.post('/api/drug/authenticate/', data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class QueueIntegrationTest(TransactionTestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name="Hospital 1",
            address="123 Main Street",
            city="New York",
            state="New York",
            email="<EMAIL>",
            phone="0123456789",
            longitude=3.339844,
            latitude=6.555475,
        )

        self.hospital2 = Hospital.objects.create(
            name="Hospital 2",
            address="123 Main Street",
            city="New York",
            state="New York",
            email="hospital2@email.com",
            phone="012345",
            longitude=3.339844,
            latitude=6.555475,
        )

        self.patient = Patient.objects.create(
            first_name="Patient 1",
            last_name="<NAME>",
            email="<EMAIL>",
            phone="0123456789",
            address="123 Main Street",
            date_of_birth=datetime.date(1999, 12, 25),
            status="RETURNING",
            hospital=self.hospital,
        )

        queue_number = Queue.objects.create(
            patient=self.patient,
            hospital=self.hospital,
            queue_number=1,
            queue_status='WAITING',

        )

        self.patient2 = Patient.objects.create(
            first_name="Patient 2",
            last_name="<NAME>",
            email="email2@email.com",
            phone="0123456789",
            address="123 Main Street",
            date_of_birth=datetime.date(1999, 12, 25),
            status="RETURNING",
            hospital=self.hospital,
        )
        self.patient3 = Patient.objects.create(
            first_name="Patient 2",
            last_name="<NAME>",
            email="email3@email.com",
            phone="01234567",
            address="123 Main Street",
            date_of_birth=datetime.date(1999, 12, 25),
            status="RETURNING",
            hospital=self.hospital,
        )

    async def test_websocket_receives_queue_update_on_post(self):
        hospital_id = 1
        communicator = WebsocketCommunicator(application, f"ws/queue/join/{hospital_id}/")

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        def trigger_post():
            client = APIClient()
            url = reverse("join-queue", kwargs={'hospital_id': hospital_id})
            payload = {
                "patient": self.patient2.id
            }
            return client.post(url, data=payload, format='json')

        response = await database_sync_to_async(trigger_post)()
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_ws = await communicator.receive_from()
        data = json.loads(response_ws)
        # print(data)

        self.assertEqual(data['new_queue_count'], 2)
        await communicator.disconnect()

    async def test_websocket_receives_queue_status_on_update(self):
        hospital_id = 1
        communicator = WebsocketCommunicator(application, f"ws/queue/update/{self.patient.id}/")
        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        def trigger_update():
            client = APIClient()
            url = reverse("update-queue", kwargs={'patient_id': self.patient.id})
            payload = {
                "queue_status": "CALLED"
            }
            return client.put(url, data=payload, format='json')

        response = await database_sync_to_async(trigger_update)()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_ws = await communicator.receive_from()
        data = json.loads(response_ws)

        self.assertEqual(data['new_queue_status'], 'CALLED')
        await communicator.disconnect()
