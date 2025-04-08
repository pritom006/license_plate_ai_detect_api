from django.contrib import admin
from .models import User,LicensePlate,AIDetectedLicense

# Register your models here.
admin.site.register(User)
admin.site.register(LicensePlate)
admin.site.register(AIDetectedLicense)
