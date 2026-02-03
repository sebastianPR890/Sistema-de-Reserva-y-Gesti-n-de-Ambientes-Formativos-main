from django.contrib import admin
from .models import Notificacion

@admin.register(Notificacion)
class notificacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'fecha_de_creacion', 'leida')
    list_filter = ('leida', 'tipo', 'fecha_de_creacion')
    search_fields = ('titulo', 'mensaje', 'usuario__documento', 'usuario__email')
    actions = ['marcar_como_leida']
    
    def marcar_como_leida(self, request, queryset):
        queryset.update(leida=True)
        self.message_user(request, f"{queryset.count()} notificaciones marcadas como leídas")
    
    marcar_como_leida.short_description = "Marcar como leída"