import socket
import netifaces
from zeroconf import ServiceInfo, Zeroconf
import json
import uuid
import os

class DeviceDiscovery:
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.service_name = None
        self.service_info = None
        self.device_id = self._get_or_create_device_id()
        
    def _get_or_create_device_id(self):
        """Get or create a unique device ID"""
        id_file = os.path.expanduser('~/.remote_control_device_id')
        if os.path.exists(id_file):
            with open(id_file, 'r') as f:
                return f.read().strip()
        device_id = str(uuid.uuid4())
        with open(id_file, 'w') as f:
            f.write(device_id)
        return device_id
        
    def _get_ip_address(self):
        """Get the device's IP address"""
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):  # Skip localhost
                        return ip
        return None

    def _get_hostname(self):
        """Get the device's hostname"""
        return socket.gethostname()
        
    def start_broadcasting(self, port):
        """Start broadcasting the service"""
        ip_address = self._get_ip_address()
        if not ip_address:
            raise Exception("No suitable network interface found")
            
        hostname = self._get_hostname()
        service_type = "_remotecontrol._tcp.local."
        self.service_name = f"{hostname}-{self.device_id}{service_type}"
        
        # Prepare service info
        properties = {
            'device_id': self.device_id,
            'hostname': hostname,
            'os': 'linux'  # You can add more properties as needed
        }
        
        self.service_info = ServiceInfo(
            service_type,
            self.service_name,
            addresses=[socket.inet_aton(ip_address)],
            port=port,
            properties=properties,
            server=f"{hostname}.local."
        )
        
        self.zeroconf.register_service(self.service_info)
        
    def stop_broadcasting(self):
        """Stop broadcasting the service"""
        if self.service_info:
            self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
            self.service_info = None 