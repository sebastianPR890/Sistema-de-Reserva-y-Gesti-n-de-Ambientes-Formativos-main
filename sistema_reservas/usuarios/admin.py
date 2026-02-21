from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, SolicitudCambioRol


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin personalizado que oculta campos redundantes sincronizados automáticamente."""

    list_display = ('documento', 'nombres', 'apellidos', 'email', 'rol', 'activo')
    list_filter = ('rol', 'activo', 'is_staff')
    search_fields = ('documento', 'nombres', 'apellidos', 'email')
    ordering = ('apellidos', 'nombres')

    # username, first_name, last_name se sincronizan automáticamente en save()
    # No se muestran para evitar edición directa y desincronización
    fieldsets = (
        (None, {'fields': ('documento', 'password')}),
        ('Información personal', {'fields': ('nombres', 'apellidos', 'email', 'telefono')}),
        ('Rol y estado', {'fields': ('rol', 'activo')}),
        ('Permisos', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('documento', 'nombres', 'apellidos', 'email', 'password1', 'password2', 'rol'),
        }),
    )


@admin.register(SolicitudCambioRol)
class SolicitudCambioRolAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol_actual', 'rol_solicitado', 'estado', 'fecha_solicitud')
    list_filter = ('estado',)
    search_fields = ('usuario__documento', 'usuario__nombres', 'usuario__apellidos')
    readonly_fields = ('fecha_solicitud', 'fecha_respuesta')
