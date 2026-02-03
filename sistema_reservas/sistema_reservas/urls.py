from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reservas.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('ambientes/', include('ambientes.urls')),
    path('equipos/', include('equipos.urls')),
    path('notificaciones/', include('notificaciones.urls')),
    path('accounts/', include('login.urls')),
    path('backups/', include('backups.urls')),
    path('calendario/', include('calendario.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # type: ignore