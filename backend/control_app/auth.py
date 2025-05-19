from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.conf import settings
import secrets
import string

def generate_pairing_code():
    """Generate a 6-digit pairing code"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

# Store pairing codes temporarily (in production, use Redis or similar)
PAIRING_CODES = {}

@api_view(['POST'])
@permission_classes([AllowAny])
def request_pairing(request):
    """Generate a pairing code for device connection"""
    code = generate_pairing_code()
    device_id = request.data.get('device_id')
    
    if not device_id:
        return Response({'error': 'Device ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Store the pairing code with device ID
    PAIRING_CODES[code] = {
        'device_id': device_id,
        'used': False
    }
    
    return Response({
        'pairing_code': code,
        'expires_in': 300  # 5 minutes
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_pairing(request):
    """Verify pairing code and create authentication tokens"""
    code = request.data.get('code')
    device_id = request.data.get('device_id')
    
    if not code or not device_id:
        return Response(
            {'error': 'Both code and device_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify the pairing code
    if code not in PAIRING_CODES or PAIRING_CODES[code]['used']:
        return Response(
            {'error': 'Invalid or expired pairing code'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if PAIRING_CODES[code]['device_id'] != device_id:
        return Response(
            {'error': 'Device ID mismatch'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark code as used
    PAIRING_CODES[code]['used'] = True
    
    # Create or get user for the device
    username = f"device_{device_id}"
    user, created = User.objects.get_or_create(username=username)
    
    if created:
        user.set_password(secrets.token_urlsafe(32))
        user.save()
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }) 