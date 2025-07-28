from django.urls import path
from .views import (LoginView, Verify2FAView, Setup2FAView,
                    logout_view, 
                    check_session_status, )

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('verify/', Verify2FAView.as_view(), name='verify-2fa'),
    path('setup/', Setup2FAView.as_view(), name='setup-2fa'),
    path('logout/', logout_view, name='logout'),
    path('check-session-status/', check_session_status, name='check_session_status'),
]