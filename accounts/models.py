from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from .managers import UserManager



class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    def name(self):
        return self.first_name + " " +self.last_name

    def __str__(self):
        return self.email



class LicensePlate(models.Model):
    """Model to store user-submitted license plate numbers"""
    plate_number = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_plates')
    timestamp = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.plate_number


class AIDetectedLicense(models.Model):
    """Model to store license plates detected by the AI model"""
    plate_number = models.CharField(max_length=20)
    detection_timestamp = models.DateTimeField(auto_now_add=True)
    snapshot_path = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.plate_number