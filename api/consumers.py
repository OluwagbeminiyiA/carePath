import json
from channels.generic.websocket import AsyncWebsocketConsumer


class UpdateHospitalQueueCountConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.hospital_id = self.scope['url_route']['kwargs']['hospital_id']
        self.room_name = f"hospital_{self.hospital_id}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def queue_update(self, event):
        await self.send(text_data=json.dumps({
            'new_queue_count': event['count'],
        }))


class UpdatePatientQueueStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.patient_id = self.scope['url_route']['kwargs']['patient_id']
        self.room_name = f"patient_{self.patient_id}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def queue_status_update(self, event):
        await self.send(text_data=json.dumps({
            'new_queue_status': event['status'],
        }))
