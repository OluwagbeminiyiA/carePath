from random import randint

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import Hospital, Patient, Queue


class HospitalSerializer(serializers.ModelSerializer):
    queue_count = serializers.SerializerMethodField()
    estimated_waiting_time = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = '__all__'

    @extend_schema_field(OpenApiTypes.INT)
    def get_queue_count(self, obj):
        return obj.queues.filter(queue_status="WAITING").count()

    @extend_schema_field(OpenApiTypes.STR)
    def get_estimated_waiting_time(self, obj):
        avg_time_per_patient = randint(30, 45)
        count = self.get_queue_count(obj)

        total_minutes = count * avg_time_per_patient

        # Return a readable string
        if total_minutes < 60:
            return f"{total_minutes} mins"
        else:
            hours = total_minutes // 60
            mins = total_minutes % 60
            return f"{hours}h {mins}m"


class PatientDetailSerializer(serializers.ModelSerializer):
    hospital = serializers.PrimaryKeyRelatedField(queryset=Hospital.objects.all())

    class Meta:
        model = Patient
        fields = '__all__'

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['hospital'] = HospitalSerializer(instance.hospital).data
        return response


class PatientQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        exclude = ['hospital']


class QueueSerializer(serializers.ModelSerializer):
    hospital = HospitalSerializer()
    patient = PatientQueueSerializer()

    class Meta:
        model = Queue
        fields = '__all__'


class JoinQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = '__all__'


class QueueUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = '__all__'
        read_only_fields = ['queue_number', 'hospital', 'patient', ]


class DrugCheckSerializer(serializers.Serializer):
    drug_image = serializers.ImageField()
    symptoms = serializers.CharField(max_length=1000)


class DrugCheckResponseSerializer(serializers.Serializer):
    drug_identified = serializers.CharField()
    is_suitable = serializers.BooleanField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    explanation = serializers.CharField()


class DrugAuthenticationSerializer(serializers.Serializer):
    drug_image = serializers.ImageField()


class DrugAuthenticationResponseSerializer(serializers.Serializer):
    drug_identified = serializers.CharField()
    is_authentic = serializers.BooleanField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    explanation = serializers.CharField()
