from django.shortcuts import render
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json
import logging
import os
from .discovery import DeviceDiscovery
from .agent import (
    get_system_info,
    get_running_processes,
    list_applications,
    list_directory,
    launch_application as launch_app,
    read_file_content,
    write_file_content,
    delete_file,
    create_directory,
    get_file_info,
    create_zip_archive,
    handle_file_upload,
    extract_zip,
    take_screenshot,
    get_music_players,
    control_music_player,
    get_local_music,
    play_local_file,
    kill_process,
    open_application,
    open_file
)
import socket
import uuid
import zeroconf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Store active pairing codes temporarily
PAIRING_CODES = {}

class DeviceDiscoveryService:
    def __init__(self):
        self.zc = zeroconf.Zeroconf()
        self.service_type = "_shellsync._tcp.local."
        self.local_device = None
        self.register_local_device()

    def register_local_device(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        self.local_device = {
            'id': str(uuid.uuid4()),
            'name': hostname,
            'ip': ip_address,
            'port': 8000,
        }
        
        info = zeroconf.ServiceInfo(
            self.service_type,
            f"{hostname}.{self.service_type}",
            addresses=[socket.inet_aton(ip_address)],
            port=8000,
            properties={
                'id': self.local_device['id'],
                'name': hostname,
            }
        )
        
        self.zc.register_service(info)

    def discover_devices(self):
        # In a real implementation, this would use zeroconf to discover other devices
        # For now, we'll just return the local device
        return [
            {
                'id': self.local_device['id'],
                'name': self.local_device['name'],
                'ip': self.local_device['ip'],
                'status': 'available'
            }
        ]

    def close(self):
        self.zc.close()

# Create a global instance
discovery_service = DeviceDiscoveryService()

@api_view(['GET'])
@permission_classes([AllowAny])
def discover_devices(request):
    """Discover available devices on the network."""
    devices = discovery_service.discover_devices()
    return Response({'devices': devices})

@api_view(['POST'])
@permission_classes([AllowAny])
def request_pairing(request):
    """Generate a pairing code for device connection."""
    device_id = request.data.get('device_id')
    if not device_id:
        return Response({'error': 'Device ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate a 6-digit pairing code
    pairing_code = str(uuid.uuid4().int)[:6]
    
    # Store the pairing code with expiration
    PAIRING_CODES[device_id] = {
        'code': pairing_code,
        'expires_at': datetime.now() + timedelta(minutes=5)
    }
    
    return Response({'pairing_code': pairing_code})

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_pairing(request):
    """Verify pairing code and generate access tokens."""
    device_id = request.data.get('device_id')
    code = request.data.get('code')
    
    if not device_id or not code:
        return Response(
            {'error': 'Device ID and code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if pairing code exists and is valid
    pairing_info = PAIRING_CODES.get(device_id)
    if not pairing_info or pairing_info['code'] != code:
        return Response(
            {'error': 'Invalid pairing code'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if code has expired
    if datetime.now() > pairing_info['expires_at']:
        PAIRING_CODES.pop(device_id, None)
        return Response(
            {'error': 'Pairing code has expired'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate tokens
    refresh = RefreshToken.for_user(request.user)
    
    # Remove used pairing code
    PAIRING_CODES.pop(device_id, None)
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    })

@api_view(['POST'])
def disconnect(request):
    """Handle device disconnection."""
    # Clear any session data if needed
    return Response({'status': 'disconnected'})

# Protected endpoints that require authentication
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_info(request):
    try:
        info = get_system_info()
        logger.debug(f"System info retrieved: {info}")
        return JsonResponse(info)
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def running_processes(request):
    try:
        processes = get_running_processes()
        return JsonResponse({'processes': processes})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def applications(request):
    try:
        apps = list_applications()
        return JsonResponse({'applications': apps})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def launch_application(request):
    try:
        data = json.loads(request.body)
        app_id = data.get('app_id')
        result = launch_app(app_id)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def open_file_handler(request):
    try:
        data = json.loads(request.body)
        file_path = data.get('path')
        if not file_path:
            return JsonResponse({'error': 'path is required'}, status=400)
        
        result = open_file(file_path)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def directory(request):
    try:
        path = request.GET.get('path', '~')
        contents = list_directory(path)
        return JsonResponse({'contents': contents}, safe=True)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def read_file(request):
    try:
        file_path = request.GET.get('path')
        if not file_path:
            return JsonResponse({'error': 'path is required'}, status=400)
            
        result = read_file_content(file_path)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def download_file(request):
    try:
        file_path = request.GET.get('path')
        if not file_path:
            return JsonResponse({'error': 'path is required'}, status=400)
            
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'File not found'}, status=404)
            
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
    except PermissionError:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def write_file(request):
    try:
        data = json.loads(request.body)
        file_path = data.get('path')
        content = data.get('content')
        use_sudo = data.get('use_sudo', False)
        
        if not file_path or content is None:
            return JsonResponse({'error': 'path and content are required'}, status=400)
            
        result = write_file_content(file_path, content, use_sudo)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_dir(request):
    try:
        data = json.loads(request.body)
        dir_path = data.get('path')
        use_sudo = data.get('use_sudo', False)
        
        if not dir_path:
            return JsonResponse({'error': 'path is required'}, status=400)
            
        result = create_directory(dir_path, use_sudo)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_item(request):
    try:
        if request.method == "DELETE":
            path = request.GET.get('path')
            use_sudo = request.GET.get('use_sudo', '').lower() == 'true'
        else:  # POST
            data = json.loads(request.body)
            path = data.get('path')
            use_sudo = data.get('use_sudo', False)
            
        if not path:
            return JsonResponse({'error': 'path is required'}, status=400)
            
        result = delete_file(path, use_sudo)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def file_info(request):
    try:
        file_path = request.GET.get('path')
        if not file_path:
            return JsonResponse({'error': 'path is required'}, status=400)
            
        result = get_file_info(file_path)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def download_item(request):
    """Download a file or directory (as zip)"""
    temp_dir = None
    try:
        path = request.GET.get('path')
        if not path:
            return JsonResponse({'error': 'path is required'}, status=400)
            
        if not os.path.exists(path):
            return JsonResponse({'error': 'Path not found'}, status=404)
            
        if os.path.isdir(path):
            # Create zip archive for directory
            result = create_zip_archive(path)
            if 'error' in result:
                return JsonResponse(result, status=500)
                
            # Get the temporary directory path from the zip path
            temp_dir = os.path.dirname(result['zip_path'])
            
            try:
                response = FileResponse(open(result['zip_path'], 'rb'))
                response['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
                return response
            finally:
                # Clean up the temporary directory in a finally block
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            # Single file download
            response = FileResponse(open(path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
            return response
    except PermissionError:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    except Exception as e:
        # Clean up temp dir if it exists
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """Handle file upload"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
            
        target_path = request.POST.get('path', '/')
        use_sudo = request.POST.get('use_sudo', 'false').lower() == 'true'
        
        uploaded_file = request.FILES['file']
        file_data = uploaded_file.read()
        
        result = handle_file_upload(
            file_data,
            target_path,
            uploaded_file.name,
            use_sudo
        )
        
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def extract_zip_file(request):
    """Extract a zip file"""
    try:
        data = json.loads(request.body)
        zip_path = data.get('zip_path')
        target_dir = data.get('target_dir')
        use_sudo = data.get('use_sudo', False)
        
        if not zip_path or not target_dir:
            return JsonResponse({'error': 'zip_path and target_dir are required'}, status=400)
            
        result = extract_zip(zip_path, target_dir, use_sudo)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def screenshot(request):
    try:
        result = take_screenshot()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def music_players(request):
    """Get list of music players and their status"""
    try:
        result = get_music_players()
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def control_player(request):
    """Control a music player"""
    try:
        data = json.loads(request.body)
        player_name = data.get('player')
        action = data.get('action')
        
        if not player_name or not action:
            return JsonResponse({'error': 'player and action are required'}, status=400)
            
        result = control_music_player(player_name, action)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def local_music(request):
    """Get list of local music files"""
    try:
        result = get_local_music()
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def play_music(request):
    """Play a local music file"""
    try:
        data = json.loads(request.body)
        file_path = data.get('path')
        
        if not file_path:
            return JsonResponse({'error': 'path is required'}, status=400)
            
        result = play_local_file(file_path)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def kill_process(request):
    try:
        data = json.loads(request.body)
        pid = data.get('pid')
        use_sudo = data.get('use_sudo', False)
        
        if not pid:
            return JsonResponse({'error': 'pid is required'}, status=400)
            
        result = kill_process(pid, use_sudo)
        if result['status'] == 'error':
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
