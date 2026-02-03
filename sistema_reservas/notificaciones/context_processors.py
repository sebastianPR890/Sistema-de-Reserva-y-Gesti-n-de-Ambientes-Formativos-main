# notificaciones/context_processors.py
from .models import Notificacion

def notificaciones_no_leidas_count(request):
    if request.user.is_authenticated:
        count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
        return {'notificaciones_no_leidas_count': count}
    return {'notificaciones_no_leidas_count': 0}

