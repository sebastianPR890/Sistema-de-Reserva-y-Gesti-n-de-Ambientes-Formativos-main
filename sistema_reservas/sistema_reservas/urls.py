from django.conf import settings
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path, include
from django.conf.urls.static import static


class SuperuserAdminSite(AdminSite):
    """Panel de administración de Django restringido exclusivamente a superusuarios."""
    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


admin.site.__class__ = SuperuserAdminSite

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
    path('actividad/', include('actividad.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # type: ignore