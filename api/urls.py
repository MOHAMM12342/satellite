from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from two_factor.urls import urlpatterns as tf_urls  
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', include(tf_urls)),
    path('admin/', admin.site.urls),
    path('api/', include('myapi.urls')),
    path('accounts/login/', RedirectView.as_view(url='/admin/login/')),
    path('iprestrict/', include('iprestrict.urls', namespace='iprestrict')),
]