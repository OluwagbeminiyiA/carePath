from django.urls import path
from .views import (
    QueueListView, JoinQueueView,
    HospitalListView, HospitalCreateView,
    PatientListView, PatientCreateView, HospitalDetailView, PatientDetailView, QueueDetailForPatient, QueueUpdateView,
    DrugValidityCheckView, DrugAuthenticationCheckView
)

urlpatterns = [
    path('queue/list/', QueueListView.as_view(), name='queue-list'),
    path('queue/find/<int:patient_id>/', QueueDetailForPatient.as_view(), name='queue-detail'),
    path('queue/join/<int:hospital_id>/', JoinQueueView.as_view(), name='join-queue'),
    path('queue/update/<int:patient_id>/', QueueUpdateView.as_view(), name='update-queue'),
    path('hospitals/list/', HospitalListView.as_view(), name='hospital-list'),
    path('hospital/create/', HospitalCreateView.as_view(), name='hospital-create'),
    path('hospital/<int:pk>/', HospitalDetailView.as_view(), name='hospital-detail'),
    path('patients/list/', PatientListView.as_view(), name='patient-list'),
    path('patient/create/', PatientCreateView.as_view(), name='patient-create'),
    path('patient/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),
    path('drug/check/', DrugValidityCheckView.as_view(), name='drug-check'),
    path('drug/authenticate/', DrugAuthenticationCheckView.as_view(), name='drug-authenticate'),
]
