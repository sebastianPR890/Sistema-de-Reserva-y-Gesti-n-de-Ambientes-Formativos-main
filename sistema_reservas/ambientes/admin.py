from django.contrib import admin
from .models import Ambiente


@admin.register(Ambiente)
class AmbienteAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista de ambientes
    list_display = (
        'codigo', 'nombre', 'tipo', 'capacidad', 
        'ubicacion', 'activo', 'fecha_creacion'
    )
    
    # Campos que permiten filtrar la lista de ambientes
    list_filter = ('tipo', 'activo', 'fecha_creacion')
    
    # Campos por los cuales se puede buscar
    search_fields = ('codigo', 'nombre', 'ubicacion')
    
    # Campos que se pueden editar directamente desde la lista
    list_editable = ('activo',)
    
    # Ordena la lista por el campo 'codigo' por defecto
    ordering = ('codigo',)
    
    # Agrupa campos en el formulario de edición para una mejor organización
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'tipo', 'ubicacion')
        }),
        ('Capacidad y Estado', {
            'fields': ('capacidad', 'activo')
        }),
    )

    # para mostrar los recursos
    readonly_fields = ('get_recursos_display',)
    
