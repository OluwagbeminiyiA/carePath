from django.contrib import admin
from .models import Hospital, Patient, Queue

# Register your models here.
admin.site.register(Hospital)
admin.site.register(Patient)
admin.site.register(Queue)
