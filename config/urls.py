"""
URL configuration for content_mentor project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import homepage, api_root

urlpatterns = [
    path('', homepage, name='homepage'),
    path('api-info/', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/', include('apps.content.urls')),
    path('api/', include('apps.access_control.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
