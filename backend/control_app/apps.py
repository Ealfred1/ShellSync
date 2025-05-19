from django.apps import AppConfig
from django.conf import settings


class ControlAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'control_app'
    
    def ready(self):
        """Initialize device discovery service when app starts"""
        # Only start discovery service in the main process
        import os
        if os.environ.get('RUN_MAIN'):
            from .discovery import DeviceDiscovery
            # Get the port from settings or default to 8000
            port = getattr(settings, 'PORT', 8000)
            discovery = DeviceDiscovery()
            discovery.start_broadcasting(port)
