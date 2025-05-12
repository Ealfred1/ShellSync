from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import os
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
    get_file_info
)

logger = logging.getLogger(__name__)

# Create your views here.

@csrf_exempt
@require_http_methods(["GET"])
def system_info(request):
    try:
        info = get_system_info()
        logger.debug(f"System info retrieved: {info}")  # Debug log
        return JsonResponse(info)
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def running_processes(request):
    try:
        processes = get_running_processes()
        return JsonResponse({'processes': processes})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def applications(request):
    try:
        apps = list_applications()
        return JsonResponse({'applications': apps})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def launch_application(request):
    try:
        data = json.loads(request.body)
        app_path = data.get('app_path')
        if not app_path:
            return JsonResponse({'error': 'app_path is required'}, status=400)
        
        result = launch_app(app_path)
        if 'error' in result:
            return JsonResponse(result, status=500)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def directory(request):
    try:
        path = request.GET.get('path', '/')
        contents = list_directory(path)
        return JsonResponse({'contents': contents})
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
