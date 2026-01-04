from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/queue/join/(?P<hospital_id>\d+)/$', consumers.UpdateHospitalQueueCountConsumer.as_asgi()),
    re_path(r'ws/queue/update/(?P<patient_id>\d+)/$', consumers.UpdatePatientQueueStatusConsumer.as_asgi()),
]