from django.apps import AppConfig


class ActividadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'actividad'
    verbose_name = 'Registro de Actividad'

    def ready(self):
        import actividad.signals  # noqa: F401
