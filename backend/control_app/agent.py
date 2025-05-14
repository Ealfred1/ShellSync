import os
import psutil
import subprocess
import json
from pathlib import Path
from datetime import datetime
import platform
import socket
import netifaces
import time
import shutil
import tempfile
import zipfile
from typing import Dict, Any, Union
from PIL import ImageGrab
import dbus
import glob

def get_system_info():
    """Get comprehensive system information"""
    # Basic system info
    system = platform.system()
    release = platform.release()
    machine = platform.machine()
    processor = platform.processor()
    hostname = socket.gethostname()

    # CPU info
    cpu_freq = psutil.cpu_freq()
    cpu_info = {
        'percent': psutil.cpu_percent(interval=1),
        'cores': psutil.cpu_count(),
        'physical_cores': psutil.cpu_count(logical=False),
        'frequency': {
            'current': cpu_freq.current if cpu_freq else None,
            'min': cpu_freq.min if cpu_freq else None,
            'max': cpu_freq.max if cpu_freq else None
        },
        'temperature': get_cpu_temperature()
    }

    # Memory info
    memory = psutil.virtual_memory()
    memory_info = {
        'total': memory.total,
        'available': memory.available,
        'used': memory.used,
        'percent': memory.percent,
        'swap': dict(psutil.swap_memory()._asdict())
    }

    # Disk info
    disk = psutil.disk_usage('/')
    disk_info = {
        'total': disk.total,
        'free': disk.free,
        'used': disk.used,
        'percent': disk.percent
    }

    # Battery info
    battery = get_battery_info()

    # Network info
    network_info = get_network_info()

    # Date and time
    now = datetime.now()
    time_info = {
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S'),
        'timezone': datetime.now().astimezone().tzname(),
        'timestamp': int(now.timestamp())
    }

    # Active windows
    active_windows = get_active_windows()

    return {
        'system': {
            'os': system,
            'release': release,
            'machine': machine,
            'processor': processor,
            'hostname': hostname,
            'uptime': get_uptime()
        },
        'cpu': cpu_info,
        'memory': memory_info,
        'disk': disk_info,
        'battery': battery,
        'network': network_info,
        'time': time_info,
        'active_windows': active_windows
    }

def get_cpu_temperature():
    """Get CPU temperature if available"""
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            return temps['coretemp'][0].current
        return None
    except:
        return None

def get_battery_info():
    """Get battery information"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            return {
                'percent': battery.percent,
                'power_plugged': battery.power_plugged,
                'time_left': battery.secsleft if battery.secsleft != -1 else None
            }
        return None
    except:
        return None

def get_network_info():
    """Get network interfaces information"""
    network_info = {}
    
    # Get network interfaces
    interfaces = netifaces.interfaces()
    
    for interface in interfaces:
        try:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                network_info[interface] = {
                    'ip': addrs[netifaces.AF_INET][0]['addr'],
                    'netmask': addrs[netifaces.AF_INET][0]['netmask']
                }
        except:
            continue
    
    # Get network usage
    net_io = psutil.net_io_counters()
    network_info['usage'] = {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv
    }
    
    return network_info

def get_uptime():
    """Get system uptime in seconds"""
    return int(time.time() - psutil.boot_time())

def get_active_windows():
    """Get list of active windows using wmctrl"""
    try:
        output = subprocess.check_output(['wmctrl', '-l']).decode()
        windows = []
        for line in output.splitlines():
            parts = line.split(None, 3)
            if len(parts) >= 4:
                windows.append({
                    'id': parts[0],
                    'desktop': parts[1],
                    'host': parts[2],
                    'title': parts[3]
                })
        return windows
    except:
        return []

def get_running_processes():
    """Get list of running processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'cpu_percent': proc.info['cpu_percent'],
                'memory_percent': proc.info['memory_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes

def parse_desktop_file(file_path):
    """Parse a .desktop file and extract relevant information"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            data = {}
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()
            return {
                'name': data.get('Name', ''),
                'exec': data.get('Exec', ''),
                'icon': data.get('Icon', ''),
                'path': file_path,
                'description': data.get('Comment', '')
            }
    except:
        return None

def list_applications():
    """List available desktop applications"""
    apps = []
    app_dirs = [
        '/usr/share/applications/',
        os.path.expanduser('~/.local/share/applications/')
    ]
    
    for app_dir in app_dirs:
        if os.path.exists(app_dir):
            for file in os.listdir(app_dir):
                if file.endswith('.desktop'):
                    app_path = os.path.join(app_dir, file)
                    app_data = parse_desktop_file(app_path)
                    if app_data and app_data['exec']:  # Only add if we have a valid exec command
                        apps.append(app_data)
    return apps

def list_directory(path='/'):
    """List contents of a directory"""
    try:
        path = os.path.expanduser(path)
        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            try:
                stat = os.stat(full_path)
                items.append({
                    'name': item,
                    'path': full_path,
                    'is_dir': os.path.isdir(full_path),
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except:
                continue
        return items
    except Exception as e:
        return {'error': str(e)}

def launch_application(app_path, use_sudo=False, sudo_password=None):
    """Launch an application from its .desktop file"""
    try:
        if not app_path.endswith('.desktop'):
            return {'error': 'Not a valid desktop entry file'}
            
        app_data = parse_desktop_file(app_path)
        if not app_data or not app_data['exec']:
            return {'error': 'Invalid desktop entry or missing Exec field'}
            
        # Extract the base command (remove any arguments after %)
        exec_cmd = app_data['exec'].split('%')[0].strip()
        
        # Split the command into parts and remove any quotes
        cmd_parts = [part.strip('"\'') for part in exec_cmd.split()]
        
        # Get current user's environment
        user_env = os.environ.copy()
        
        if use_sudo:
            if not sudo_password:
                return {'error': 'sudo_password_required', 'message': 'Please provide sudo password'}
            
            # Create a wrapper script that sets up the environment
            script_content = f"""#!/bin/bash
export DISPLAY="{os.environ.get('DISPLAY', ':0')}"
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/{os.getuid()}/bus"
export XDG_RUNTIME_DIR="/run/user/{os.getuid()}"
{' '.join(cmd_parts)}
"""
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            os.chmod(temp_script, 0o755)
            
            try:
                # Use sudo with the wrapper script
                cmd = ['sudo', '-S', '-E', temp_script]
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=user_env,
                    text=True
                )
                stdout, stderr = process.communicate(input=f"{sudo_password}\n")
                
                if process.returncode != 0:
                    if "incorrect password" in stderr.lower():
                        return {'error': 'incorrect_password', 'message': 'Incorrect sudo password'}
                    return {'error': f'Failed to launch: {stderr}'}
            finally:
                # Clean up the temporary script
                try:
                    os.unlink(temp_script)
                except:
                    pass
        else:
            # Launch directly without sudo
            subprocess.Popen(cmd_parts, env=user_env, start_new_session=True)
            
        return {'status': 'success', 'command': exec_cmd}
    except PermissionError:
        return {'error': 'sudo_password_required', 'message': 'Permission denied. Please provide sudo password.'}
    except Exception as e:
        return {'error': str(e)}

def terminate_process(pid):
    """Terminate a process by PID"""
    try:
        process = psutil.Process(pid)
        process.terminate()
        return {'status': 'success'}
    except Exception as e:
        return {'error': str(e)}

def read_file_content(file_path):
    """Read the content of a file"""
    try:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            return {'error': 'File does not exist'}
        if not os.path.isfile(file_path):
            return {'error': 'Path is not a file'}
            
        with open(file_path, 'r') as f:
            content = f.read()
            return {
                'content': content,
                'size': os.path.getsize(file_path),
                'modified': os.path.getmtime(file_path)
            }
    except PermissionError:
        return {'error': 'Permission denied. Try with sudo.'}
    except Exception as e:
        return {'error': str(e)}

def write_file_content(file_path, content, use_sudo=False):
    """Write content to a file"""
    try:
        file_path = os.path.expanduser(file_path)
        
        if use_sudo:
            # Write content to temporary file
            temp_path = '/tmp/temp_file_content'
            with open(temp_path, 'w') as f:
                f.write(content)
            # Use sudo to move the file
            subprocess.run(['sudo', 'mv', temp_path, file_path], check=True)
            # Set proper permissions
            subprocess.run(['sudo', 'chmod', '644', file_path], check=True)
        else:
            with open(file_path, 'w') as f:
                f.write(content)
                
        return {'status': 'success'}
    except PermissionError:
        return {'error': 'Permission denied. Try with sudo.'}
    except Exception as e:
        return {'error': str(e)}

def delete_file(file_path, use_sudo=False):
    """Delete a file or directory"""
    try:
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            return {'error': 'Path does not exist'}
            
        if use_sudo:
            subprocess.run(['sudo', 'rm', '-rf', file_path], check=True)
        else:
            if os.path.isdir(file_path):
                os.rmdir(file_path)
            else:
                os.remove(file_path)
                
        return {'status': 'success'}
    except PermissionError:
        return {'error': 'Permission denied. Try with sudo.'}
    except Exception as e:
        return {'error': str(e)}

def create_directory(dir_path, use_sudo=False):
    """Create a new directory"""
    try:
        dir_path = os.path.expanduser(dir_path)
        
        if os.path.exists(dir_path):
            return {'error': 'Path already exists'}
            
        if use_sudo:
            subprocess.run(['sudo', 'mkdir', '-p', dir_path], check=True)
            subprocess.run(['sudo', 'chmod', '755', dir_path], check=True)
        else:
            os.makedirs(dir_path)
            
        return {'status': 'success'}
    except PermissionError:
        return {'error': 'Permission denied. Try with sudo.'}
    except Exception as e:
        return {'error': str(e)}

def get_file_info(file_path):
    """Get detailed information about a file"""
    try:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            return {'error': 'Path does not exist'}
            
        stat = os.stat(file_path)
        return {
            'name': os.path.basename(file_path),
            'path': file_path,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'accessed': stat.st_atime,
            'mode': stat.st_mode,
            'is_dir': os.path.isdir(file_path),
            'is_file': os.path.isfile(file_path),
            'is_link': os.path.islink(file_path),
            'owner': stat.st_uid,
            'group': stat.st_gid,
            'permissions': oct(stat.st_mode)[-3:]
        }
    except PermissionError:
        return {'error': 'Permission denied'}
    except Exception as e:
        return {'error': str(e)}

def create_zip_archive(path: str) -> Dict[str, Any]:
    """Create a zip archive of a directory"""
    try:
        import os
        import tempfile
        import shutil
        from pathlib import Path
        
        # Ensure path exists and is a directory
        if not os.path.exists(path):
            return {'error': 'Path does not exist'}
        if not os.path.isdir(path):
            return {'error': 'Path is not a directory'}
            
        # Create a temporary directory that will definitely exist
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create zip file name based on directory name
            dir_name = os.path.basename(path.rstrip('/'))
            zip_name = f"{dir_name}.zip"
            zip_path = os.path.join(temp_dir, zip_name)
            
            # Create the zip archive
            shutil.make_archive(
                os.path.join(temp_dir, dir_name),  # Base name (without .zip)
                'zip',  # Format
                path  # Root directory to zip
            )
            
            return {
                'zip_path': zip_path,
                'filename': zip_name
            }
            
        except Exception as e:
            # Clean up temp dir in case of error
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {'error': str(e)}
            
    except Exception as e:
        return {'error': str(e)}

def handle_file_upload(file_data: bytes, target_path: str, filename: str, use_sudo: bool = False) -> Dict[str, Any]:
    """Handle file upload to a specific directory"""
    try:
        target_path = os.path.expanduser(target_path)
        if not os.path.exists(target_path):
            return {'error': 'Target directory does not exist'}
        
        if not os.path.isdir(target_path):
            return {'error': 'Target path is not a directory'}
            
        file_path = os.path.join(target_path, filename)
        
        if use_sudo:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            # Use sudo to move the file to target location
            subprocess.run(['sudo', 'mv', temp_path, file_path], check=True)
            subprocess.run(['sudo', 'chmod', '644', file_path], check=True)
        else:
            with open(file_path, 'wb') as f:
                f.write(file_data)
        
        return {'status': 'success', 'path': file_path}
    except PermissionError:
        return {'error': 'Permission denied. Try with sudo.'}
    except Exception as e:
        return {'error': str(e)}

def extract_zip(zip_path: str, target_dir: str, use_sudo: bool = False) -> Dict[str, Any]:
    """Extract a zip file to a target directory"""
    try:
        zip_path = os.path.expanduser(zip_path)
        target_dir = os.path.expanduser(target_dir)
        
        if not os.path.exists(zip_path):
            return {'error': 'Zip file does not exist'}
            
        if not os.path.exists(target_dir):
            return {'error': 'Target directory does not exist'}
            
        if use_sudo:
            # Extract to temporary directory first
            with tempfile.TemporaryDirectory() as temp_dir:
                shutil.unpack_archive(zip_path, temp_dir, 'zip')
                # Move contents to target directory with sudo
                subprocess.run(['sudo', 'cp', '-r', f"{temp_dir}/*", target_dir], check=True)
                subprocess.run(['sudo', 'chmod', '-R', '644', target_dir], check=True)
        else:
            shutil.unpack_archive(zip_path, target_dir, 'zip')
            
        return {'status': 'success'}
    except PermissionError:
        return {'error': 'Permission denied. Try with sudo.'}
    except Exception as e:
        return {'error': str(e)}

def take_screenshot() -> Dict[str, Any]:
    """Take a screenshot and save it"""
    try:
        # Create screenshots directory if it doesn't exist
        screenshots_dir = os.path.expanduser('~/Screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'screenshot_{timestamp}.png'
        filepath = os.path.join(screenshots_dir, filename)
        
        # Try different screenshot methods
        try:
            # First try using gnome-screenshot
            subprocess.run(['gnome-screenshot', '-f', filepath], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try using import from ImageMagick
                subprocess.run(['import', '-window', 'root', filepath], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    # Try using scrot as fallback
                    subprocess.run(['scrot', filepath], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # If all else fails, use PIL
                    screenshot = ImageGrab.grab()
                    screenshot.save(filepath)
        
        if os.path.exists(filepath):
            return {
                'status': 'success',
                'path': filepath,
                'filename': filename
            }
        else:
            return {'error': 'Failed to save screenshot'}
            
    except Exception as e:
        return {'error': str(e)}

def get_music_players() -> Dict[str, Any]:
    """Get list of available music players and their status"""
    try:
        bus = dbus.SessionBus()
        players = []
        
        # Check for running players
        for service in bus.list_names():
            if service.startswith('org.mpris.MediaPlayer2.'):
                try:
                    player_name = service.split('.')[-1]
                    player_obj = bus.get_object(service, '/org/mpris/MediaPlayer2')
                    player_interface = dbus.Interface(player_obj, 'org.mpris.MediaPlayer2.Player')
                    player_properties = dbus.Interface(player_obj, 'org.freedesktop.DBus.Properties')
                    
                    metadata = player_properties.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                    playback_status = player_properties.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                    
                    players.append({
                        'name': player_name,
                        'status': playback_status,
                        'current_track': {
                            'title': metadata.get('xesam:title', ''),
                            'artist': metadata.get('xesam:artist', [''])[0],
                            'album': metadata.get('xesam:album', ''),
                            'url': metadata.get('xesam:url', '')
                        }
                    })
                except:
                    continue
        
        return {
            'status': 'success',
            'players': players
        }
    except Exception as e:
        return {'error': str(e)}

def control_music_player(player_name: str, action: str) -> Dict[str, Any]:
    """Control a music player (play/pause/next/previous)"""
    try: 
        bus = dbus.SessionBus()
        service = f'org.mpris.MediaPlayer2.{player_name}'
          
        if service not in bus.list_names(): 
            return {'error': 'Player not found'}
            
        player_obj = bus.get_object(service, '/org/mpris/MediaPlayer2')
        player_interface = dbus.Interface(player_obj, 'org.mpris.MediaPlayer2.Player')
        
        actions = {
            'play': player_interface.Play,
            'pause': player_interface.Pause,
            'playpause': player_interface.PlayPause,
            'next': player_interface.Next,
            'previous': player_interface.Previous
        }
        
        if action not in actions:
            return {'error': 'Invalid action'}
            
        actions[action]()
        return {'status': 'success'}
    except Exception as e:
        return {'error': str(e)}

def get_local_music() -> Dict[str, Any]:
    """Get list of music files in common music directories""" 
    try:
        music_dirs = [
            os.path.expanduser('~/Music'),
            '/usr/share/sounds'
        ]
        
        music_files = []
        for music_dir in music_dirs:
            if os.path.exists(music_dir):
                for ext in ['*.mp3', '*.m4a', '*.ogg', '*.flac', '*.wav']:
                    pattern = os.path.join(music_dir, '**', ext)
                    music_files.extend(glob.glob(pattern, recursive=True))
        
        files = []
        for file_path in music_files:
            try:
                stat = os.stat(file_path)
                files.append({
                    'name': os.path.basename(file_path),
                    'path': file_path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except:
                continue
                
        return {
            'status': 'success',
            'files': files
        }
    except Exception as e:
        return {'error': str(e)}

def play_local_file(file_path: str) -> Dict[str, Any]: 
    """Play a local music file using default audio player"""
    try:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            return {'error': 'File not found'}
            
        
        subprocess.Popen(['xdg-open', file_path], start_new_session=True)
        return {'status': 'success'}
    except Exception as e:
        return {'error': str(e)}

def kill_process(pid: int, use_sudo: bool = False) -> Dict[str, str]:
    """
    Kill a process by PID
    """
    try:
        if use_sudo:
            subprocess.run(['sudo', 'kill', str(pid)], check=True)
        else:
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
    except subprocess.CalledProcessError:
        return {
            "status": "error",
            "message": f"Failed to terminate process {pid} with sudo"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to terminate process {pid}: {str(e)}"
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