from rest_framework import serializers
from .models import User, LicensePlate, AIDetectedLicense

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'is_verified']

class VerifyAccountSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()


class LicensePlateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicensePlate
        fields = ['id', 'plate_number', 'timestamp', 'verified']
        read_only_fields = ['id', 'timestamp', 'verified']


class AIDetectedLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIDetectedLicense
        fields = ['id', 'plate_number', 'detection_timestamp', 'snapshot_path']
        read_only_fields = ['id', 'detection_timestamp']