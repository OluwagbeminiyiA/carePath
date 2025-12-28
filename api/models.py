import uuid

from django.db import models
from django.db.models import UniqueConstraint
from django_lifecycle import LifecycleModelMixin, hook, BEFORE_UPDATE, AFTER_UPDATE

# Create your models here.

PATIENT_STATUS_CHOICES = (
    ('NEW', 'new'),
    ('RETURNING', 'returning'),
)

QUEUE_STATUS_CHOICES = (
    ('WAITING', 'waiting'),
    ('CALLED', 'Called'),
    ('COMPLETED', 'completed'),

)


class Hospital(LifecycleModelMixin, models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=100)
    longitude = models.FloatField()
    latitude = models.FloatField()

    def __str__(self):
        return f"{self.name} at {self.address}"


class Patient(LifecycleModelMixin, models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    status = models.CharField(max_length=100, choices=PATIENT_STATUS_CHOICES)
    patient_id = models.CharField(max_length=100, default=uuid.uuid4)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='patients_hospital')

    def __str__(self):
        return f"{self.status} patient {self.first_name} {self.last_name}."


class Queue(LifecycleModelMixin, models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='queues')
    queue_number = models.IntegerField()
    queue_status = models.CharField(max_length=100, choices=QUEUE_STATUS_CHOICES)
    time_joined = models.DateTimeField(auto_now_add=True)

    @hook(AFTER_UPDATE, when="queue_status", was='WAITING', is_now='CALLED')
    def update_queue(self):
        # This is here so the queue number goes to zero, and it doesn't cause integrity errors when the other numbers reduce because it has to be unique
        Queue.objects.filter(
            queue_number=self.queue_number,
        ).update(queue_number=self.queue_number - 1)

        Queue.objects.filter(
            queue_number__gt=self.queue_number,
            queue_status='waiting',
        ).update(queue_number=models.F('queue_number') - 1)

    @hook(AFTER_UPDATE, when="queue_status", was='CALLED', is_now='COMPLETED')
    def delete_queue(self):
        Queue.objects.filter(
            queue_status=self.queue_status,
        ).delete()

    def __str__(self):
        return f"{self.hospital} {self.patient} {self.queue_number}"

    class Meta:
        ordering = ['queue_number']
        constraints = [
            UniqueConstraint(
                fields=['hospital', 'queue_number', 'time_joined'],
                name="unique_queue_number_per_hospital"
            )
        ]
