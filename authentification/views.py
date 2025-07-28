from django.contrib.auth import authenticate, logout, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.permissions import IsAuthenticated
from two_factor.utils import default_device
from django.http import JsonResponse
import pyqrcode
from io import BytesIO
import base64
import logging
from django.db import transaction
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

logger = logging.getLogger(__name__)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        remember = request.data.get('remember', False)
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Log the user in
            login(request, user)
            
            # Debug all devices
            devices = TOTPDevice.objects.filter(user=user, confirmed=True)
            logger.info(f"All confirmed TOTP devices for {username}: {list(devices)}")
            device = default_device(user)
            logger.info(f"Default 2FA device for {username}: {device}")
            if device:
                logger.info(f"2FA required for {username}, device: {device.name}, ID: {device.id}")
                return Response({
                    'status': '2fa_required',
                    'user_id': user.id,
                    'remember': remember
                }, status=status.HTTP_200_OK)
            
            logger.info(f"No 2FA device for {username}, proceeding with login")
            return Response({
                'user': {
                    'username': user.username,
                    'is_superuser': user.is_superuser
                }
            }, status=status.HTTP_200_OK)
        
        logger.error(f"Authentication failed for {username}")
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class Verify2FAView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        token = request.data.get('token')
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            device = default_device(user)
            if device and device.verify_token(token):
                login(request, user)
                return Response({
                    'user': {
                        'username': user.username,
                        'is_superuser': user.is_superuser
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Invalid user'}, status=status.HTTP_401_UNAUTHORIZED)

class Setup2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if default_device(user):
            logger.info(f"2FA already enabled for user {user.username}")
            return Response({'error': '2FA already enabled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Clear unconfirmed devices
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()
        device = TOTPDevice.objects.create(user=user, name=user.username, confirmed=False)
        logger.info(f"Created TOTP device for {user.username}: ID={device.id}, name={device.name}")
        qr = pyqrcode.create(device.config_url)
        buffer = BytesIO()
        qr.png(buffer, scale=5)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            'qr_code': f"data:image/png;base64,{qr_base64}",
            'secret_key': device.key,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        token = request.data.get('token')
        
        with transaction.atomic():
            device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
            if device:
                logger.info(f"Verifying TOTP token for {user.username}, device ID={device.id}")
                if device.verify_token(token):
                    device.confirmed = True
                    device.save()
                    logger.info(f"TOTP device confirmed and saved for {user.username}: ID={device.id}, name={device.name}, confirmed={device.confirmed}")
                    # Verify device in DB
                    saved_device = TOTPDevice.objects.filter(user=user, id=device.id, confirmed=True).first()
                    if saved_device:
                        logger.info(f"Confirmed device found in DB for {user.username}: ID={saved_device.id}")
                    else:
                        logger.error(f"Failed to find confirmed device for {user.username}")
                    return Response({'status': '2FA enabled successfully'}, status=status.HTTP_200_OK)
                else:
                    logger.warning(f"Invalid TOTP token for {user.username}, device ID={device.id}")
                    return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.error(f"No unconfirmed TOTP device found for {user.username}")
                return Response({'error': 'No 2FA device found'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """Simplified logout view"""
    logout(request)
    request.session.flush()
    return Response({
        "message": "Logged out successfully.",
        "redirect": "/login/"
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow all to check session status
def check_session_status(request):
    """Check if the user is authenticated and session is valid"""
    if not request.user.is_authenticated:
        logger.info("Session check: User not authenticated")
        return JsonResponse({
            'authenticated': False,
            'expired': True,
            'redirect': '/login/'
        }, status=401)
    
    # Update last activity timestamp
    request.session['last_activity'] = timezone.now().isoformat()
    logger.info(f"Session check: User {request.user.username} authenticated")
    
    return JsonResponse({
        'authenticated': True,
        'session_type': 'basic'
    })