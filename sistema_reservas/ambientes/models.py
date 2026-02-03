from django.db import models
from django.utils import timezone

class Ambiente(models.Model):
    """Modelo que representa un ambiente formativo."""
    
    TIPOS = [
        ('aula', 'Aula'),
        ('laboratorio', 'Laboratorio'),
        ('taller', 'Taller'),
        ('auditorio', 'Auditorio'),
        ('biblioteca', 'Biblioteca'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    capacidad = models.PositiveIntegerField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    ubicacion = models.CharField(max_length=100, blank=True)
    recursos = models.JSONField(default=dict, blank=True, null=True, help_text="JSON con recursos disponibles")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ambiente'
        verbose_name_plural = 'Ambientes'
        db_table = 'ambientes'
        ordering = ['codigo']
        
    def get_recursos_display(self):
        """Retorna los recursos del ambiente."""
        return self.recursos
        
    def esta_disponible(self, fecha_inicio, fecha_fin, exclude_reserva_id=None):
        """Verifica si el ambiente está disponible en un rango de fechas."""
        from reservas.models import Reserva
        
        reservas_conflicto = Reserva.objects.filter(
            ambiente=self,
            estado__in= ['pendiente', 'aprobada'],
        ).filter(
            models.Q(fecha_inicio__lt=fecha_fin, fecha_fin__gt=fecha_inicio)
        )
        if exclude_reserva_id:
            reservas_conflicto = reservas_conflicto.exclude(pk=exclude_reserva_id)
        return not reservas_conflicto.exists()
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"