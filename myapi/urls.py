from django.urls import path,include
from .views import (
    satellite_list,
    satellite_subsystems,
    subsystem_files,
    file_versions,
    file_metadata,
    download_file,
    parsed_file,
    system_status,
    search_files,
    recent_files,
    LoginView, Verify2FAView, Setup2FAView,
                    logout_view, 
                    check_session_status,
)


urlpatterns = [
    path('satellites/', satellite_list),
    path('satellites/<int:sat_id>/subsystems/', satellite_subsystems),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/', subsystem_files),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/', file_versions),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/', file_metadata),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/download/', download_file),
    path('satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/parsed/<str:format>/', parsed_file),
    path('admin/system-status/', system_status),
    path('search/files/', search_files),
    path('files/recent/', recent_files),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/verify/', Verify2FAView.as_view(), name='verify-2fa'),
    path('auth/setup/', Setup2FAView.as_view(), name='setup-2fa'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/check-session-status/', check_session_status, name='check_session_status'),
]




