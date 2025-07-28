from django.urls import path
from . import views

app_name = 'myapi'

urlpatterns = [
    path('satellites/', views.satellite_list, name='satellites'),
    path('satellites/<int:sat_id>/subsystems/', views.satellite_subsystems, name='subsystems'),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/', views.subsystem_files, name='files'),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/', views.file_versions, name='file_versions'),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/', views.file_metadata, name='file_metadata'),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/download/', views.download_file, name='file_download'),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/parsed/<str:format>/', views.parsed_file, name='parsed_file'),
    path('admin/system-status/', views.system_status, name='system_status'),
    path('account/two_factor/', views.two_factor_status, name='two_factor_status'),
]