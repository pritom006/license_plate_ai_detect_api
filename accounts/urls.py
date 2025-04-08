from django.urls import path
from .views import RegisterApi, VerifyOTP, LicensePlateAPI, AIDetectedLicenseAPI, VerifyLicensePlateAPI, ImportAIDetectedLicensesAPI


urlpatterns = [
    path('register', RegisterApi.as_view(), name="register"),
    path('verify', VerifyOTP.as_view(), name="verify"),

    # License plate endpoints
    path('license-plates', LicensePlateAPI.as_view(), name='license-plates'),
    path('ai-detected-plates', AIDetectedLicenseAPI.as_view(), name='ai-detected-plates'),
    path('verify-plate', VerifyLicensePlateAPI.as_view(), name='verify-plate'),
    path('import-ai-plates', ImportAIDetectedLicensesAPI.as_view(), name='import-ai-plates'),
]