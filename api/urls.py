from django.contrib import admin
from django.urls import path, include
from two_factor.urls import urlpatterns as tf_urls  # Correct import

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(tf_urls)),  # Correct inclusion
    path('api/', include('myapi.urls')),
    path('auth/', include('authentification.urls')),
    path('iprestrict/', include('iprestrict.urls', namespace='iprestrict')),
]