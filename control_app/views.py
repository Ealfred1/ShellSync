from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from . import agent


@csrf_exempt
@require_http_methods(["GET"])
def system_info(request):
    """
    Get system information
    """
    result = agent.get_system_info()
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def list_directory(request):
    """
    List contents of a directory
    """
    try:
        data = json.loads(request.body)
        path = data.get('path', '~')
        result = agent.list_directory(path)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON payload"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def list_applications(request):
    """
    List installed applications
    """
    result = agent.list_applications()
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["GET"])
def running_processes(request):
    """
    Get list of running processes
    """
    result = agent.get_running_processes()
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def kill_process(request):
    """
    Kill a process by PID
    """
    try:
        data = json.loads(request.body)
        pid = data.get('pid')
        
        if not pid:
            return JsonResponse({
                "status": "error",
                "message": "Process ID is required"
            }, status=400)
            
        result = agent.kill_process(int(pid))
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON payload"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def take_screenshot(request):
    """
    Take a screenshot
    """
    result = agent.take_screenshot()
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def open_application(request):
    """
    API endpoint to open an application
    """
    try:
        data = json.loads(request.body)
        target = data.get('target')
        
        if not target:
            return JsonResponse({
                "status": "error",
                "message": "Target application name is required"
            }, status=400)
            
        result = agent.open_application(target)
        return JsonResponse(result, status=200 if result["status"] == "success" else 500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON payload"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def open_file(request):
    """
    API endpoint to open a file
    """
    try:
        data = json.loads(request.body)
        target = data.get('target')
        
        if not target:
            return JsonResponse({
                "status": "error",
                "message": "Target file path is required"
            }, status=400)
            
        result = agent.open_file(target)
        return JsonResponse(result, status=200 if result["status"] == "success" else 500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON payload"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500) 