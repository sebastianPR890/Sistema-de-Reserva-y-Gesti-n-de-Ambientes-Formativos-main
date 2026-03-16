from django.db import models
from django.conf import settings

class Notificacion(models.Model):
    """Modelo para gestionar notificaciones de usuarios."""
    
    TIPOS = (
        ('reserva', 'Reserva'),
        ('equipo', 'Equipo'),
        ('sistema', 'Sistema'),
        ('alerta', 'Alerta'),
    )
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=10, choices=TIPOS, default='sistema')
    leida = models.BooleanField(default=False)
    fecha_de_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        db_table = 'notificaciones'
        ordering = ['-fecha_de_creacion']
    
    @classmethod
    def crear(cls, usuario, titulo, mensaje, tipo='sistema'):
        """Crea una notificación y envía email HTML al usuario."""
        import logging
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags

        notificacion = cls.objects.create(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo
        )

        try:
            html_content = render_to_string('email/notification.html', {'titulo': titulo, 'mensaje': mensaje, 'tipo': tipo})
            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                titulo,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except Exception:
            logging.getLogger(__name__).exception('Error al enviar email de notificación')

        return notificacion
    
    @classmethod
    def notificar_gestores(cls, titulo, mensaje, tipo='alerta'):
        """
        Crea una notificación (y envía email) a todos los coordinadores y admins activos.
        """
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()
        gestores = Usuario.objects.filter(
            rol__in=['coordinador', 'admin'],
            activo=True,
        )
        for gestor in gestores:
            cls.crear(usuario=gestor, titulo=titulo, mensaje=mensaje, tipo=tipo)

    def marcar_como_leida(self):
        """Marca la notificación como leída."""
        self.leida = True
        self.save()

    def __str__(self):
        return f"{self.titulo} - {self.usuario.nombre_completo()}"