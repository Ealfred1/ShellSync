from django.urls import path
from . import views

urlpatterns = [
    path('system-info/', views.system_info, name='system-info'),
    path('list-directory/', views.list_directory, name='list-directory'),
    path('list-applications/', views.list_applications, name='list-applications'),
    path('running-processes/', views.running_processes, name='running-processes'),
    path('kill-process/', views.kill_process, name='kill-process'),
    path('take-screenshot/', views.take_screenshot, name='take-screenshot'),
    path('open-app/', views.open_application, name='open-application'),
    path('open-file/', views.open_file, name='open-file'),
] 