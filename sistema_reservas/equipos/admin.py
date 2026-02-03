from django.contrib import admin
from .models import Equipo, MovimientoEquipo

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'nombre', 'estado', 'ubicacion_actual', 
        'responsable', 'activo', 'fecha_creacion'
    )
    list_filter = ('estado', 'activo', 'fecha_creacion')
    search_fields = ('codigo', 'nombre', 'serie', 'descripcion')
    list_editable = ('activo',)
    
    # Campo de solo lectura para la ubicación actual
    readonly_fields = ('ubicacion_actual',)
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('codigo', 'nombre', 'descripcion', 'marca', 'modelo', 'serie')
        }),
        ('Estado y Ubicación', {
            'fields': ('ambiente', 'estado', 'responsable', 'activo')
        }),
        ('Detalles de Adquisición', {
            'fields': ('fecha_adquisicion', 'valor')
        }),
    )

@admin.register(MovimientoEquipo)
class MovimientoEquipoAdmin(admin.ModelAdmin):
    list_display = (
        'equipo', 'tipo_movimiento', 'ambiente_origen', 
        'ambiente_destino', 'usuario_responsable', 'fecha_movimiento'
    )
    list_filter = ('tipo_movimiento', 'fecha_movimiento')
    search_fields = (
        'equipo__nombre', 'equipo__codigo', 
        'ambiente_origen__nombre', 'ambiente_destino__nombre',
        'usuario_responsable__documento'
    )
    ordering = ('-fecha_movimiento',)