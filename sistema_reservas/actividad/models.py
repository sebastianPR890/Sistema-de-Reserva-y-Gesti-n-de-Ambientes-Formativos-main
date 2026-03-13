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
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Actividad'
        verbose_name_plural = 'Registros de Actividad'
        db_table = 'actividad_registros'
        ordering = ['-fecha']

    def __str__(self):
        nombre = self.usuario.nombre_completo() if self.usuario else 'Sistema'
        return f"{nombre} - {self.accion} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
