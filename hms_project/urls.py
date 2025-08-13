from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Use Django's built-in auth URLs
    path('users/', include('users.urls')),
    path('patient/', include('patient.urls')),
    path('appointment/', include('appointment.urls')),
    path('billing/', include('billing.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('', include('website.urls')),  # Include website urls
    
    # Explicitly serve media files even in production
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Add static and media URL patterns for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 