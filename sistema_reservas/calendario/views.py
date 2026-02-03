from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from reservas.models import Reserva
from datetime import datetime

@require_GET
@login_required
def get_reservas(request):
    """Obtiene las reservas para mostrar en el calendario."""
    # Obtener parámetros de rango de fechas si vienen del calendario
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    reservas = Reserva.objects.select_related('ambiente', 'usuario').filter(
        estado__in=['pendiente', 'aprobada']
    )
    
    # Si el usuario no es staff, solo mostrar sus propias reservas
    if not request.user.is_staff:
        reservas = reservas.filter(usuario=request.user)
    
    # Filtrar por rango de fechas si se proporcionan
    if start and end:
        try:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            reservas = reservas.filter(
                fecha_inicio__gte=start_date,
                fecha_fin__lte=end_date
            )
        except (ValueError, AttributeError):
            return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    eventos = []
    for reserva in reservas:
        color_map = {
            'pendiente': '#ffc107',
            'aprobada': '#28a745',
            'cancelada': '#dc3545',
            'rechazada': '#6c757d',
        }
        
        eventos.append({
            'id': reserva.id,
            'title': f"{reserva.ambiente.nombre}",
            'start': reserva.fecha_inicio.isoformat(),
            'end': reserva.fecha_fin.isoformat(),
            'backgroundColor': color_map.get(reserva.estado, '#6c757d'),
            'borderColor': color_map.get(reserva.estado, '#6c757d'),
            'extendedProps': {
                'proposito': reserva.proposito,
                'usuario': reserva.usuario.get_full_name(),
                'estado': reserva.get_estado_display(),
            }
        })
    
    return JsonResponse(eventos, safe=False)


@require_GET
@login_required
def vista_calendario(request):
    """Vista que renderiza la página del calendario."""
    from django.shortcuts import render
    return render(request, 'calendario/calendario.html')