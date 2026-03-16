# reservas/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class Reserva(models.Model):
    """Modelo que representa una reserva de ambiente."""
    
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    ambiente = models.ForeignKey('ambientes.Ambiente', on_delete=models.PROTECT, related_name='reservas')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservas')
    
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    proposito = models.TextField()
    numero_asistentes = models.PositiveIntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    observaciones = models.TextField(blank=True)
    aprobada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reservas_aprobadas'
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        db_table = 'reservas'
        ordering = ['-fecha_creacion']
    
    def clean(self):
        """Valida los datos del modelo antes de guardar."""
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        if self.pk is None and self.fecha_inicio and self.fecha_inicio < timezone.now():
            raise ValidationError('No se puede crear una reserva con fecha de inicio en el pasado.')

        if self.pk is None and self.fecha_inicio:
            minimo = timezone.now() + timedelta(days=3)
            if self.fecha_inicio < minimo:
                raise ValidationError('Las reservas deben realizarse con al menos 3 días de antelación.')
        
        if self.ambiente and self.fecha_inicio and self.fecha_fin:
            if not self.ambiente.esta_disponible(self.fecha_inicio, self.fecha_fin, exclude_reserva_id=self.pk):
                raise ValidationError('El ambiente no está disponible en el horario seleccionado.')
    
    def save(self, *args, **kwargs):
        """Guarda la reserva ejecutando las validaciones."""
        self.full_clean()
        super().save(*args, **kwargs)

    def duracion_horas(self):
        """Calcula la duración de la reserva en horas."""
        if self.fecha_fin and self.fecha_inicio:
            delta = self.fecha_fin - self.fecha_inicio
            return delta.total_seconds() / 3600
        return 0
    
    def puede_ser_editada(self):
        """Verifica si la reserva puede ser editada."""
        return self.estado in ['pendiente', 'aprobada'] and self.fecha_inicio > timezone.now()
    
    def puede_ser_cancelada(self):
        """Verifica si la reserva puede ser cancelada."""
        return self.estado in ['pendiente', 'aprobada'] and self.fecha_inicio > timezone.now()
    
    def aprobar(self, usuario_aprobador):
        """Aprueba la reserva si el usuario tiene permisos."""
        if usuario_aprobador and usuario_aprobador.puede_aprobar_reservas():
            self.estado = 'aprobada'
            self.aprobada_por = usuario_aprobador
            self.fecha_aprobacion = timezone.now()
            self.save()
            return True
        return False
    
    def rechazar(self, observaciones=''):
        """Rechaza la reserva con observaciones opcionales."""
        self.estado = 'rechazada'
        if observaciones:
            self.observaciones = observaciones
        self.save()
    
    @classmethod
    def cancelar_expiradas(cls):
        """Cancela reservas pendientes que llevan más de 72 horas sin ser aprobadas."""
        limite = timezone.now() - timedelta(hours=72)
        return cls.objects.filter(estado='pendiente', fecha_creacion__lte=limite).update(estado='cancelada')

    @classmethod
    def cerrar_vencidas(cls):
        """
        Marca como 'completada' las reservas aprobadas cuya fecha_fin ya pasó.
        También retira los equipos externos registrados durante esas reservas.
        Retorna el número de reservas cerradas.
        """
        from equipos.models import Equipo
        ahora = timezone.now()
        vencidas = cls.objects.filter(estado='aprobada', fecha_fin__lt=ahora)
        ids_vencidas = list(vencidas.values_list('id', flat=True))
        if not ids_vencidas:
            return 0
        # Retirar equipos externos vinculados a estas reservas
        Equipo.objects.filter(
            es_externo=True,
            reserva_origen_id__in=ids_vencidas,
            activo=True,
        ).update(activo=False, estado='retirado')
        # Notificar a cada usuario que su reserva fue completada
        from notificaciones.models import Notificacion
        for reserva in cls.objects.filter(id__in=ids_vencidas).select_related('usuario', 'ambiente'):
            Notificacion.crear(
                usuario=reserva.usuario,
                titulo='Reserva completada',
                mensaje=(
                    f'Tu reserva del aula {reserva.ambiente.nombre} '
                    f'({reserva.fecha_inicio.strftime("%d/%m/%Y %H:%M")} – '
                    f'{reserva.fecha_fin.strftime("%d/%m/%Y %H:%M")}) '
                    f'ha finalizado. Ya no eres responsable del aula.'
                ),
                tipo='reserva',
            )
        # Marcar reservas como completadas
        cantidad = vencidas.update(estado='completada')
        return cantidad

    @classmethod
    def get_reserva_activa(cls, ambiente, usuario):
        """
        Retorna la reserva aprobada y vigente (presente o futura) para el ambiente y usuario dados.
        El usuario es responsable del aula desde que su reserva es aprobada hasta que finaliza.
        Retorna None si no existe ninguna.
        """
        ahora = timezone.now()
        return cls.objects.filter(
            ambiente=ambiente,
            usuario=usuario,
            estado='aprobada',
            fecha_fin__gte=ahora,
        ).order_by('fecha_inicio').first()

    @classmethod
    def es_responsable_activo(cls, ambiente, usuario):
        """
        Devuelve True si el usuario tiene una reserva aprobada y vigente sobre el ambiente.
        Los admins y coordinadores siempre tienen permisos independientemente de esto.
        """
        return cls.get_reserva_activa(ambiente, usuario) is not None

    def __str__(self):
        return f"Reserva {self.id} - {self.ambiente.nombre} ({self.fecha_inicio.strftime('%d/%m/%Y %H:%M')})"