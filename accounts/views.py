from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer, VerifyAccountSerializer, LicensePlateSerializer, AIDetectedLicenseSerializer
from .emails import *
from rest_framework.permissions import IsAuthenticated
from .models import AIDetectedLicense, LicensePlate
import os
from .permissions import IsVerifiedUser
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.authtoken.models import Token

# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class RegisterApi(APIView):
    def post(self, request):
        try:
            data = request.data
            email = data.get('email')
            user = User.objects.filter(email=email).first()

            if user:
                # Update existing user's OTP and set is_verified=False
                user.is_verified = False
                user.set_password(data['password'])  # Optional: update password on re-register
                user.save()
                send_otp_via_email(user.email)
                return Response({
                    'status': 200,
                    'message': 'OTP sent for verification.',
                    'data': {'email': user.email}
                })

            # If user doesn't exist, create one
            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                send_otp_via_email(serializer.data['email'])
                return Response({
                    'status': 200,
                    'message': 'Registered successfully, check your email for verification',
                    'data': serializer.data
                })

            return Response({
                'status': 400,
                'message': 'Validation failed',
                'data': serializer.errors
            })

        except Exception as e:
            return Response({
                'status': 500,
                'message': 'Internal Server Error',
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTP(APIView):
    def post(self, request):
        try:
            data = request.data
            serializer = VerifyAccountSerializer(data=data)

            if serializer.is_valid():
                email = serializer.data['email']
                otp = serializer.data['otp']

                user = User.objects.filter(email=email).first()
                if not user:
                    return Response({
                        'status': 400,
                        'message': 'This user does not exist',
                        'data': {}
                    })

                if user.otp != otp:
                    return Response({
                        'status': 400,
                        'message': 'Invalid OTP',
                        'data': {}
                    })

                # Mark as verified
                user.is_verified = True
                user.otp = None
                user.save()

                # Generate or get auth token for automatic login
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'status': 200,
                    'message': 'Your account is verified and you are now logged in',
                    'data': {
                        'email': user.email,
                        'token': token.key  # Send token for client to use in subsequent requests
                    }
                })

            return Response({
                'status': 400,
                'message': 'Invalid data',
                'data': serializer.errors
            })
        except Exception as e:
            return Response({
                'status': 500,
                'message': 'Internal Server Error',
                'error': str(e)
            })

# New APIs for license plate functionality
class LicensePlateAPI(APIView):
    #permission_classes = [IsVerifiedUser]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({'status': 400, 'message': 'Email is required'})

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'status': 404, 'message': 'User not found'})

            serializer = LicensePlateSerializer(data=request.data)
            if serializer.is_valid():
                plate_number = serializer.validated_data['plate_number'].strip().upper()
                ai_detected = AIDetectedLicense.objects.filter(plate_number=plate_number).exists()
                
                # Save with user and verified
                license_plate = LicensePlate.objects.create(
                    user=user,
                    plate_number=plate_number,
                    verified=ai_detected
                )

                serialized_data = LicensePlateSerializer(license_plate).data

                return Response({
                    'status': 200,
                    'message': 'License plate submitted successfully',
                    'verified': ai_detected,
                    'data': serialized_data
                })

            return Response({
                'status': 400,
                'message': 'Invalid input',
                'data': serializer.errors
            })

        except Exception as e:
            return Response({
                'status': 500,
                'message': 'Internal Server Error',
                'error': str(e)
            })
        
    
    def get(self, request):
        """Get all license plates submitted by the user"""
        try:
            email = request.data.get("email")
            if not email:
                return Response({
                    'status': 400,
                    'message': 'Email is required'
                })

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'status': 404,
                    'message': 'User not found'
                })

            plates = LicensePlate.objects.filter(user=user)
            serializer = LicensePlateSerializer(plates, many=True)

            return Response({
                'status': 200,
                'message': 'License plates retrieved successfully',
                'data': serializer.data
            })

        except Exception as e:
            return Response({
                'status': 500,
                'message': 'Internal Server Error',
                'error': str(e)
            })

class AIDetectedLicenseAPI(APIView):
    permission_classes = [IsVerifiedUser]
    
    def get(self, request):
        """Get all AI detected license plates"""
        try:
            detected_plates = AIDetectedLicense.objects.all()
            serializer = AIDetectedLicenseSerializer(detected_plates, many=True)
            
            return Response({
                'status': 200,
                'message': 'AI detected license plates retrieved successfully',
                'data': serializer.data
            })
        
        except Exception as e:
            return Response({
                'status': 500,
                'message': 'Internal Server Error',
                'error': str(e)
            })


class VerifyLicensePlateAPI(APIView):
    #permission_classes = [IsVerifiedUser]
    
    def post(self, request):
        """Verify if a specific license plate exists in AI detected plates"""
        try:
            email = request.data.get('email')
            plate_number = request.data.get('plate_number')
            
            if not email:
                return Response({
                    'status': 400,
                    'message': 'Email is required',
                })
                
            if not plate_number:
                return Response({
                    'status': 400,
                    'message': 'License plate number is required',
                })
            
            # Get the user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'status': 404,
                    'message': 'User not found',
                })
            
            # Format plate number (strip spaces and convert to uppercase)
            plate_number = plate_number.strip().upper()
            
            # Check if the license plate exists in AI detected plates
            ai_detected = AIDetectedLicense.objects.filter(plate_number=plate_number).exists()
            
            # Store the user's submission regardless of verification result
            license_plate, created = LicensePlate.objects.get_or_create(
                user=user,
                plate_number=plate_number,
                defaults={'verified': ai_detected}
            )
            
            # If plate already exists but verification status is different, update it
            if not created and license_plate.verified != ai_detected:
                license_plate.verified = ai_detected
                license_plate.save()
            
            if ai_detected:
                return Response({
                    'status': 200,
                    'message': 'License plate verified successfully',
                    'verified': True
                })
            else:
                return Response({
                    'status': 404,
                    'message': 'License plate not found in AI detected plates',
                    'verified': False
                })
        
        except Exception as e:
            return Response({
                'status': 500,
                'message': 'Internal Server Error',
                'error': str(e)
            })


class ImportAIDetectedLicensesAPI(APIView):
    """API to import AI detected license plates from the text files"""
    permission_classes = [IsVerifiedUser]
    
    def post(self, request):
        try:
            # Check if user is admin or staff
            if not request.user.is_staff:
                return Response({
                    'status': 403,
                    'message': 'Permission denied. Only staff can import AI detected licenses.'
                })
            
            # Get paths from settings or use default
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            detected_dir = os.path.join(base_dir, 'detected_texts')
            snapshot_dir = os.path.join(base_dir, 'snapshots')
            counter = 0
            
            if not os.path.exists(detected_dir):
                return Response({
                    'status': 404,
                    'message': f'Directory {detected_dir} not found'
                })
            
            # Get all text files in the detected_texts directory
            for filename in os.listdir(detected_dir):
                if filename.endswith('.txt'):
                    file_path = os.path.join(detected_dir, filename)
                    
                    # Extract timestamp from filename
                    timestamp_str = filename.replace('license_plate_', '').replace('.txt', '')
                    
                    # Read the license plate text
                    with open(file_path, 'r') as file:
                        plate_number = file.read().strip().upper()
                    
                    # Check for corresponding snapshot
                    snapshot_path = None
                    snapshot_filename = f'license_plate_{timestamp_str}.jpg'
                    if os.path.exists(os.path.join(snapshot_dir, snapshot_filename)):
                        snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
                    
                    # Create AI detected license if it doesn't exist already
                    if plate_number and not AIDetectedLicense.objects.filter(plate_number=plate_number).exists():
                        AIDetectedLicense.objects.create(
                            plate_number=plate_number,
                            snapshot_path=snapshot_path
                        )
                        counter += 1
            
            return Response({
                'status': 200,
                'message': f'Successfully imported {counter} new AI detected license plates',
            })
        
        except Exception as e:
            return Response({
                'status': 500,
                'message': 'Internal Server Error',
                'error': str(e)
            })