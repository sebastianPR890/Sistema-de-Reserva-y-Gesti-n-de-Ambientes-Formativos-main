from django.db import models
from django.conf import settings
from django.utils import timezone
from ambientes.models import Ambiente

class Equipo(models.Model):
    """Modelo que representa un equipo de cómputo o mobiliario."""

    ESTADOS = [
        ('disponible', 'Disponible'),
        ('en_uso', 'En uso'),
        ('mantenimiento', 'Mantenimiento'),
        ('dañado', 'Dañado'),
        ('retirado', 'Retirado'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=50, blank=True)
    serie = models.CharField(max_length=100, blank=True)
    ambiente = models.ForeignKey(Ambiente, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipos_responsable'
    )
    # Campos para equipos externos (no pertenecen a la institución)
    es_externo = models.BooleanField(default=False)
    propietario_externo = models.CharField(max_length=200, blank=True)
    doc_propietario = models.CharField(max_length=50, blank=True)
    reserva_origen = models.ForeignKey(
        'reservas.Reserva',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipos_externos'
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        db_table = 'equipos'
        ordering = ['codigo']
    
    def ultimo_movimiento(self):
        """Obtiene el último movimiento registrado del equipo."""
        return self.movimientos.order_by('-fecha_movimiento').first()
    
    def ubicacion_actual(self):
        """Determina la ubicación actual del equipo."""
        ultimo_mov = self.ultimo_movimiento()
        if ultimo_mov:
            if ultimo_mov.tipo_movimiento == 'entrada' and ultimo_mov.ambiente_destino:
                return ultimo_mov.ambiente_destino.nombre
            elif ultimo_mov.tipo_movimiento == 'salida' and ultimo_mov.ambiente_origen:
                return f"Fuera de {ultimo_mov.ambiente_origen.nombre}"
        if self.ambiente:
            return self.ambiente.nombre
        return "Desconocida"
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class MovimientoEquipo(models.Model):
    """Modelo para registrar movimientos de equipos entre ambientes."""
    
    TIPOS_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]
    
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPOS_MOVIMIENTO)
    ambiente_origen = models.ForeignKey(
        Ambiente, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='movimientos_origen'
    )
    ambiente_destino = models.ForeignKey(
        Ambiente, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='movimientos_destino'
    )
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='movimientos_realizados'
    )
    observaciones = models.TextField(blank=True)
    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='movimientos_autorizados'
    )
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Movimiento de Equipo'
        verbose_name_plural = 'Movimientos de Equipos'
        db_table = 'movimientos_equipos'
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        origen = self.ambiente_origen.nombre if self.ambiente_origen else 'N/A'
        destino = self.ambiente_destino.nombre if self.ambiente_destino else 'N/A'
        return f"{self.equipo.codigo} - {self.get_tipo_movimiento_display()} de {origen} a {destino} ({self.fecha_movimiento.strftime('%d/%m/%Y %H:%M')})"
