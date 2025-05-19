from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Device Discovery and Authentication
    path('discover/', views.discover_devices, name='discover_devices'),
    path('auth/request-pairing/', views.request_pairing, name='request_pairing'),
    path('auth/verify-pairing/', views.verify_pairing, name='verify_pairing'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('disconnect/', views.disconnect, name='disconnect'),

    # File System Operations
    path('list-directory/', views.list_directory, name='list_directory'),
    path('file-info/', views.file_info, name='file_info'),
    path('read-file/', views.read_file, name='read_file'),
    path('write-file/', views.write_file, name='write_file'),
    path('create-dir/', views.create_directory, name='create_directory'),
    path('delete-item/', views.delete_item, name='delete_item'),
    path('download-file/', views.download_file, name='download_file'),
    path('upload-file/', views.upload_file, name='upload_file'),
    path('extract-zip/', views.extract_zip, name='extract_zip'),

    # System Information
    path('system-info/', views.system_info, name='system_info'),
    path('running-processes/', views.running_processes, name='running_processes'),
    path('kill-process/', views.kill_process, name='kill_process'),
    path('list-applications/', views.list_applications, name='list_applications'),
    path('launch-application/', views.launch_application, name='launch_application'),
] 