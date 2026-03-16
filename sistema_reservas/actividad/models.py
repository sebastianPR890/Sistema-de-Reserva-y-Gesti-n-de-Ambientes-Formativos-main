from django.db import models
from django.conf import settings


class RegistroActividad(models.Model):
    MODULOS = [
        ('reservas', 'Reservas'),
        ('usuarios', 'Usuarios'),
        ('ambientes', 'Ambientes'),
        ('equipos', 'Equipos'),
        ('sesion', 'Sesión'),
        ('sistema', 'Sistema'),
    ]

    TIPOS_ACCION = [
        ('CREATE',  'Creación'),
        ('UPDATE',  'Modificación'),
        ('DELETE',  'Eliminación'),
        ('LOGIN',   'Inicio de sesión'),
        ('LOGOUT',  'Cierre de sesión'),
        ('APPROVE', 'Aprobación'),
        ('REJECT',  'Rechazo'),
        ('CANCEL',  'Cancelación'),
        ('EXPORT',  'Exportación'),
        ('OTHER',   'Otro'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades'
    )
    accion = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    modulo = models.CharField(max_length=20, choices=MODULOS, default='sistema')
    tipo_accion = models.CharField(max_length=20, choices=TIPOS_ACCION, default='OTHER')
    objeto_tipo = models.CharField(max_length=50, blank=True)
    objeto_id = models.PositiveIntegerField(null=True, blank=True)
    datos_antes = models.JSONField(null=True, blank=True)
    datos_despues = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Actividad'
        verbose_name_plural = 'Registros de Actividad'
        db_table = 'actividad_registros'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['modulo']),
            models.Index(fields=['tipo_accion']),
            models.Index(fields=['usuario']),
            models.Index(fields=['fecha']),
            models.Index(fields=['objeto_tipo', 'objeto_id']),
            models.Index(fields=['modulo', 'fecha']),
            models.Index(fields=['usuario', 'fecha']),
        ]

    def __str__(self):
        nombre = self.usuario.nombre_completo() if self.usuario else 'Sistema'
        return f"{nombre} - {self.accion} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
