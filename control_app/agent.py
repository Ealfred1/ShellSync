import subprocess
import os
import glob
import psutil
from typing import Dict, List, Optional
from datetime import datetime


def get_system_info() -> Dict[str, str]:
    """
    Get basic system information
    """
    try:
        info = {
            "os": os.uname().sysname,
            "hostname": os.uname().nodename,
            "cpu_count": psutil.cpu_count(),
            "memory_total": f"{psutil.virtual_memory().total / (1024*1024*1024):.2f}GB",
            "memory_available": f"{psutil.virtual_memory().available / (1024*1024*1024):.2f}GB",
            "disk_usage": f"{psutil.disk_usage('/').percent}%"
        }
        return {"status": "success", "data": info}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_directory(path: str = "~") -> Dict[str, any]:
    """
    List contents of a directory
    """
    try:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"status": "error", "message": "Path does not exist"}

        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            item_info = {
                "name": item,
                "path": full_path,
                "type": "directory" if os.path.isdir(full_path) else "file",
                "size": os.path.getsize(full_path) if os.path.isfile(full_path) else None,
                "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
            }
            items.append(item_info)

        return {"status": "success", "data": items}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_applications() -> Dict[str, any]:
    """
    List installed applications in common locations
    """
    try:
        app_dirs = ["/usr/share/applications", "~/.local/share/applications"]
        apps = []
        
        for app_dir in app_dirs:
            app_dir = os.path.expanduser(app_dir)
            if os.path.exists(app_dir):
                desktop_files = glob.glob(os.path.join(app_dir, "*.desktop"))
                for desktop_file in desktop_files:
                    try:
                        with open(desktop_file, 'r') as f:
                            content = f.read()
                            name = None
                            exec_cmd = None
                            for line in content.split('\n'):
                                if line.startswith('Name='):
                                    name = line.split('=')[1]
                                elif line.startswith('Exec='):
                                    exec_cmd = line.split('=')[1].split(' ')[0]
                            if name and exec_cmd:
                                apps.append({"name": name, "command": exec_cmd})
                    except:
                        continue

        return {"status": "success", "data": apps}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_running_processes() -> Dict[str, any]:
    """
    Get list of running processes
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent']):
            try:
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "user": proc.info['username'],
                    "memory": f"{proc.info['memory_percent']:.1f}%"
                })
            except:
                continue
        return {"status": "success", "data": processes}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def take_screenshot() -> Dict[str, str]:
    """
    Take a screenshot using scrot
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.expanduser(f"~/Pictures/{filename}")
        
        # Ensure Pictures directory exists
        os.makedirs(os.path.expanduser("~/Pictures"), exist_ok=True)
        
        process = subprocess.run(["scrot", filepath], 
                               capture_output=True, 
                               text=True)
        
        if process.returncode == 0:
            return {
                "status": "success",
                "message": "Screenshot taken successfully",
                "path": filepath
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to take screenshot: {process.stderr}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Screenshot error: {str(e)}"
        }


def open_application(app_name: str) -> Dict[str, str]:
    """
    Launch a GUI application using subprocess
    """
    try:
        process = subprocess.Popen([app_name], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        return {
            "status": "success",
            "message": f"Application {app_name} launched successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to launch {app_name}: {str(e)}"
        }


def open_file(file_path: str) -> Dict[str, str]:
    """
    Open a file using the system's default application
    """
    try:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"File {file_path} does not exist"
            }
            
        process = subprocess.Popen(["xdg-open", file_path],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return {
            "status": "success",
            "message": f"File {file_path} opened successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to open {file_path}: {str(e)}"
        }


def kill_process(pid: int) -> Dict[str, str]:
    """
    Kill a process by PID
    """
    try:
        process = psutil.Process(pid)
        process.terminate()
        return {
            "status": "success",
            "message": f"Process {pid} terminated successfully"
        }
    except psutil.NoSuchProcess:
        return {
            "status": "error",
            "message": f"Process {pid} not found"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to terminate process {pid}: {str(e)}"
        } 