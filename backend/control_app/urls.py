from django.urls import path
from . import views

urlpatterns = [
    path('system-info/', views.system_info, name='system-info'),
    path('running-processes/', views.running_processes, name='running-processes'),
    path('list-applications/', views.applications, name='list-applications'),
    path('launch-application/', views.launch_application, name='launch-application'),
    path('open-file/', views.open_file_handler, name='open-file'),
    path('list-directory/', views.directory, name='list-directory'),
    path('kill-process/', views.kill_process, name='kill-process'),
    path('take-screenshot/', views.screenshot, name='take-screenshot'),
    path('local-music/', views.local_music, name='local-music'),
    path('music-players/', views.music_players, name='music-players'),
    path('control-player/', views.control_player, name='control-player'),
    path('play-music/', views.play_music, name='play-music'),
    path('file-info/', views.file_info, name='file-info'),
    path('read-file/', views.read_file, name='read-file'),
    path('download-file/', views.download_file, name='download-file'),
    path('download-item/', views.download_item, name='download-item'),
    path('write-file/', views.write_file, name='write-file'),
    path('create-dir/', views.create_dir, name='create-dir'),
    path('delete-item/', views.delete_item, name='delete-item'),
    path('upload-file/', views.upload_file, name='upload-file'),
    path('extract-zip/', views.extract_zip_file, name='extract-zip'),
] 