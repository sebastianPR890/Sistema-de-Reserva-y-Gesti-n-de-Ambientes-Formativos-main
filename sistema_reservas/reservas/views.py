from django.utils import timezone
import io
import json
from datetime import datetime
from copy import deepcopy

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

from ambientes.models import Ambiente
from notificaciones.models import Notificacion
from actividad.utils import registrar_actualizacion, capturar_cambios, registrar_actividad, capturar_todos_campos
from .utils import registrar_cambio_reserva
from .models import Reserva
from .forms import ReservaForm

def index(request):
    """Vista principal."""
    return render(request, 'index.html')

@login_required
def lista_reservas(request):
    """Muestra la lista de reservas según el tipo de usuario."""
    Reserva.cancelar_expiradas()
    if request.user.puede_gestionar_recursos():
        reservas = Reserva.objects.select_related('usuario', 'ambiente').all()
        user_type = 'admin'
    else:
        reservas = Reserva.objects.select_related('ambiente').filter(usuario=request.user)
        user_type = 'user'
    
    # Contadores para el dashboard
    total_reservas = reservas.count()
    reservas_pendientes = reservas.filter(estado='pendiente').count()
    reservas_aprobadas = reservas.filter(estado='aprobada').count()
    reservas_canceladas = reservas.filter(estado='cancelada').count()
    
    context = {
        'reservas': reservas,
        'total_reservas': total_reservas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_aprobadas': reservas_aprobadas,
        'reservas_canceladas': reservas_canceladas,
        'user_type': user_type,
    }
    
    return render(request, 'reservas/lista_reservas.html', context)


MAX_RESERVAS_ACTIVAS = 2

@login_required
def crear_reserva(request):
    """Permite crear una nueva reserva."""
    if request.user.rol == 'usuario':
        messages.error(request, 'Necesitas un rol asignado para poder crear reservas. Solicita cambio de rol primero.')
        return redirect('/')

    reservas_activas = Reserva.objects.filter(
        usuario=request.user,
        estado__in=['pendiente', 'aprobada'],
        fecha_fin__gt=timezone.now()
    ).count()
    if reservas_activas >= MAX_RESERVAS_ACTIVAS:
        messages.error(
            request,
            f'No puedes tener más de {MAX_RESERVAS_ACTIVAS} reservas activas simultáneamente. '
            f'Cancela o espera a que finalicen las existentes.'
        )
        return redirect('reservas:lista_reservas')

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.save()
            registrar_actividad(
                usuario=request.user,
                accion=f'Reserva creada: {reserva.ambiente.nombre}',
                descripcion=f'Desde: {reserva.fecha_inicio.strftime("%d/%m/%Y %H:%M")} | Hasta: {reserva.fecha_fin.strftime("%d/%m/%Y %H:%M")} | Propósito: {reserva.proposito}',
                modulo='reservas',
                tipo_accion='CREATE',
                objeto=reserva,
                request=request,
            )
            Notificacion.crear(
                usuario=request.user,
                titulo='Reserva Creada',
                mensaje=f'Tu reserva ha sido creada y está pendiente de aprobación.',
                tipo='reserva'
            )
            messages.success(request, '¡Reserva creada exitosamente!')
            return redirect('reservas:lista_reservas')
    else:
        form = ReservaForm()
    return render(request, 'reservas/crear_reserva.html', {'form': form})


@login_required
def editar_reserva(request, pk):
    """Permite editar una reserva existente."""
    reserva = get_object_or_404(Reserva, pk=pk)

    if reserva.usuario != request.user and not request.user.puede_gestionar_recursos():
        return HttpResponseForbidden("No tienes permiso para editar esta reserva.")

    if not reserva.puede_ser_editada():
        messages.error(request, 'Esta reserva ya no puede ser editada.')
        return redirect('reservas:lista_reservas')

    if reserva.estado == 'aprobada' and not request.user.is_staff:
        messages.error(request, 'Las reservas aprobadas solo pueden ser modificadas por un administrador.')
        return redirect('reservas:lista_reservas')

    if request.method == 'POST':
        # Capturar estado ANTES
        datos_antes = capturar_todos_campos(reserva)

        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            reserva_actualizada = form.save()

            # Capturar estado DESPUÉS
            datos_despues = capturar_todos_campos(reserva_actualizada)

            # Comparar cambios
            cambios = {}
            for campo, valor_antes in datos_antes.items():
                valor_despues = datos_despues.get(campo)
                if valor_antes != valor_despues:
                    cambios[campo] = {
                        'antes': valor_antes,
                        'después': valor_despues
                    }

            # Construir descripción
            descripcion_cambios = ""
            if cambios:
                cambios_formateados = []
                for campo, valores in cambios.items():
                    antes = valores.get('antes', '')
                    despues = valores.get('después', '')
                    cambios_formateados.append(f"{campo}: {antes} → {despues}")
                descripcion_cambios = "\n".join(cambios_formateados)

            registrar_actividad(
                usuario=request.user,
                accion=f'Reserva actualizada: {reserva.pk}',
                descripcion=descripcion_cambios if descripcion_cambios else 'Sin cambios detectados',
                modulo='reservas',
                tipo_accion='UPDATE',
                objeto=reserva_actualizada,
                datos_antes=datos_antes if cambios else None,
                datos_despues=datos_despues if cambios else None,
                request=request
            )

            if cambios:
                # Registrar en el historial de la reserva
                registrar_cambio_reserva(
                    reserva_antes=reserva,
                    reserva_despues=reserva_actualizada,
                    usuario=request.user,
                    descripcion=descripcion_cambios
                )

            Notificacion.crear(
                usuario=request.user,
                titulo='Reserva Actualizada',
                mensaje=f'Tu reserva ha sido actualizada correctamente.',
                tipo='reserva'
            )
            messages.success(request, '¡Reserva actualizada exitosamente!')
            return redirect('reservas:lista_reservas')
    else:
        form = ReservaForm(instance=reserva)
    return render(request, 'reservas/editar_reserva.html', {'form': form})


@login_required
@login_required
def descargar_reporte_pdf(request):
    """Genera y descarga un reporte PDF de las reservas."""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph("Reporte de Reservas", title_style))
    
    if request.user.puede_gestionar_recursos():
        reservas = Reserva.objects.select_related('usuario', 'ambiente').all()
    else:
        reservas = Reserva.objects.filter(usuario=request.user).select_related('ambiente')
    
    data = [['Ambiente', 'Fecha Inicio', 'Fecha Fin', 'Estado']]
    for reserva in reservas:
        data.append([
            reserva.ambiente.nombre,
            reserva.fecha_inicio.strftime("%d/%m/%Y %H:%M"),
            reserva.fecha_fin.strftime("%d/%m/%Y %H:%M"),
            reserva.get_estado_display()
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f'reporte_reservas_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf',
        content_type='application/pdf'
    )

def manual_usuario(request):
    """Muestra el manual de usuario en HTML."""
    return render(request, 'manual/manual_usuario.html')

@login_required
@require_POST
def aprobar_reserva(request, pk):
    """Aprueba una reserva específica."""
    if not request.user.puede_gestionar_recursos():
        messages.error(request, "No tienes permisos para aprobar reservas.")
        return redirect('reservas:lista_reservas')

    reserva = get_object_or_404(Reserva, pk=pk)

    if reserva.estado != 'pendiente':
        messages.warning(request, "Solo se pueden aprobar reservas en estado pendiente.")
        return redirect('reservas:lista_reservas')

    estado_anteriormente = reserva.estado
    
    if not reserva.aprobar(request.user):
        messages.error(request, "No se pudo aprobar la reserva.")
        return redirect('reservas:lista_reservas')

    # Registrar la actualización
    cambios = {
        'estado': {
            'antes': 'Pendiente',
            'después': 'Aprobada'
        }
    }
    registrar_actualizacion(
        usuario=request.user,
        objeto=f'Reserva {reserva.pk}',
        cambios=cambios,
        modulo='reservas',
        request=request
    )

    Notificacion.crear(
        usuario=reserva.usuario,
        titulo='Reserva Aprobada',
        mensaje=f'Tu reserva para el {reserva.fecha_inicio.strftime("%d/%m/%Y")} ha sido aprobada.',
        tipo='reserva'
    )

    messages.success(request, "Reserva aprobada exitosamente.")
    return redirect('reservas:lista_reservas')

@login_required
@require_POST
def cancelar_reserva(request, pk):
    """Cancela una reserva: coordinadores pueden cancelar cualquiera; usuarios solo las propias pendientes."""
    reserva = get_object_or_404(Reserva, pk=pk)

    es_dueno = reserva.usuario == request.user
    es_gestor = request.user.puede_gestionar_recursos()

    if not es_gestor and not (es_dueno and reserva.estado == 'pendiente'):
        messages.error(request, "No tienes permisos para cancelar esta reserva.")
        return redirect('reservas:lista_reservas')

    if not reserva.puede_ser_cancelada():
        messages.warning(request, "Esta reserva no puede ser cancelada.")
        return redirect('reservas:lista_reservas')

    estado_anterior = reserva.estado
    reserva.estado = 'cancelada'
    reserva.save()

    # Registrar la actualización
    cambios = {
        'estado': {
            'antes': 'Aprobada' if estado_anterior == 'aprobada' else 'Pendiente',
            'después': 'Cancelada'
        }
    }
    registrar_actualizacion(
        usuario=request.user,
        objeto=f'Reserva {reserva.pk}',
        cambios=cambios,
        modulo='reservas',
        request=request
    )

    Notificacion.crear(
        usuario=reserva.usuario,
        titulo='Reserva Cancelada',
        mensaje=f'Tu reserva para el {reserva.fecha_inicio.strftime("%d/%m/%Y")} ha sido cancelada.',
        tipo='reserva'
    )

    messages.success(request, "Reserva cancelada exitosamente.")
    return redirect('reservas:lista_reservas')

@login_required
def rechazar_reserva(request, pk):
    """Rechaza una reserva con motivo obligatorio."""
    if not request.user.puede_gestionar_recursos():
        messages.error(request, "No tienes permisos para rechazar reservas.")
        return redirect('reservas:lista_reservas')

    reserva = get_object_or_404(Reserva, pk=pk)

    if reserva.estado != 'pendiente':
        messages.warning(request, "Solo se pueden rechazar reservas en estado pendiente.")
        return redirect('reservas:lista_reservas')

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, "El motivo del rechazo es obligatorio.")
            return render(request, 'reservas/rechazar_reserva.html', {'reserva': reserva})

        reserva.rechazar(observaciones=motivo)

        registrar_actualizacion(
            usuario=request.user,
            objeto=f'Reserva {reserva.pk}',
            cambios={'estado': {'antes': 'Pendiente', 'después': 'Rechazada'}},
            modulo='reservas',
            request=request
        )

        Notificacion.crear(
            usuario=reserva.usuario,
            titulo='Reserva Rechazada',
            mensaje=(
                f'Tu reserva del ambiente {reserva.ambiente.nombre} '
                f'para el {reserva.fecha_inicio.strftime("%d/%m/%Y")} ha sido rechazada. '
                f'Motivo: {motivo}'
            ),
            tipo='reserva'
        )

        messages.success(request, "Reserva rechazada correctamente.")
        return redirect('reservas:lista_reservas')

    return render(request, 'reservas/rechazar_reserva.html', {'reserva': reserva})


@login_required
@require_GET
def obtener_reservas_calendario(request):
    """API para obtener reservas en formato FullCalendar con parámetros específicos."""
    ambiente_id = request.GET.get('ambiente_id')
    
    # Parámetros de rango de fechas de FullCalendar
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # ambiente_id es obligatorio solo para el endpoint de creación
    if not ambiente_id:
        return JsonResponse({'error': 'ambiente_id requerido'}, status=400)
    
    try:
        ambiente = Ambiente.objects.get(pk=ambiente_id)
    except Ambiente.DoesNotExist:
        return JsonResponse({'error': 'Ambiente no encontrado'}, status=404)
    
    # Obtener reservas del ambiente
    reservas_queryset = Reserva.objects.filter(
        ambiente=ambiente,
        estado__in=['pendiente', 'aprobada']
    ).select_related('usuario')
    
    # Filtrar por rango de fechas si se proporcionan
    if start and end:
        try:
            # Manejar diferentes formatos de fecha
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            reservas_queryset = reservas_queryset.filter(
                fecha_inicio__gte=start_date,
                fecha_fin__lte=end_date
            )
        except (ValueError, AttributeError, TypeError):
            pass  # Si hay error, mostrar todos
    
    eventos = []
    for reserva in reservas_queryset:
        color_map = {
            'pendiente': '#ffc107',
            'aprobada': '#28a745',
            'cancelada': '#dc3545',
            'rechazada': '#6c757d',
        }
        
        eventos.append({
            'id': reserva.id,
            'title': f"{reserva.usuario.get_full_name()} - {reserva.proposito[:30]}",
            'start': reserva.fecha_inicio.isoformat(),
            'end': reserva.fecha_fin.isoformat(),
            'backgroundColor': color_map.get(reserva.estado, '#6c757d'),
            'borderColor': color_map.get(reserva.estado, '#6c757d'),
            'extendedProps': {
                'usuario': reserva.usuario.get_full_name(),
                'proposito': reserva.proposito,
                'estado': reserva.get_estado_display(),
                'numero_asistentes': reserva.numero_asistentes or 'No especificado',
            }
        })
    
    return JsonResponse(eventos, safe=False)


@login_required
@require_POST
def crear_reserva_calendario(request):
    """Crear reserva desde el calendario (AJAX)."""
    if request.user.rol == 'usuario':
        return JsonResponse({'success': False, 'error': 'Necesitas un rol asignado para crear reservas.'}, status=403)

    reservas_activas = Reserva.objects.filter(
        usuario=request.user,
        estado__in=['pendiente', 'aprobada'],
        fecha_fin__gt=timezone.now()
    ).count()
    if reservas_activas >= MAX_RESERVAS_ACTIVAS:
        return JsonResponse({
            'success': False,
            'error': f'No puedes tener más de {MAX_RESERVAS_ACTIVAS} reservas activas simultáneamente.'
        }, status=400)

    try:
        data = json.loads(request.body)
        ambiente_id = data.get('ambiente_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        proposito = data.get('proposito', '')
        numero_asistentes = data.get('numero_asistentes')
        
        if not all([ambiente_id, fecha_inicio, fecha_fin]):
            return JsonResponse({'success': False, 'error': 'Datos incompletos'}, status=400)
        
        # Convertir strings a datetime
        try:
            fecha_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
            fecha_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return JsonResponse({'success': False, 'error': 'Formato de fecha inválido'}, status=400)
        
        # Verificar disponibilidad
        try:
            ambiente = Ambiente.objects.get(pk=ambiente_id)
        except Ambiente.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ambiente no encontrado'}, status=404)
        
        if not ambiente.esta_disponible(fecha_inicio, fecha_fin):
            return JsonResponse({
                'success': False, 
                'error': 'El ambiente no está disponible en ese período'
            }, status=400)
        
        # Validar que la fecha de fin sea posterior a la de inicio
        if fecha_fin <= fecha_inicio:
            return JsonResponse({
                'success': False,
                'error': 'La fecha de fin debe ser posterior a la de inicio'
            }, status=400)
        
        # Crear reserva
        reserva = Reserva.objects.create(
            ambiente=ambiente,
            usuario=request.user,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            proposito=proposito,
            numero_asistentes=numero_asistentes
        )
        
        registrar_actividad(
            usuario=request.user,
            accion=f'Reserva creada (calendario): {ambiente.nombre}',
            descripcion=f'Desde: {fecha_inicio.strftime("%d/%m/%Y %H:%M")} | Hasta: {fecha_fin.strftime("%d/%m/%Y %H:%M")} | Propósito: {proposito}',
            modulo='reservas',
            tipo_accion='CREATE',
            objeto=reserva,
            request=request,
        )
        Notificacion.crear(
            usuario=request.user,
            titulo='Reserva Creada',
            mensaje=f'Tu reserva en {ambiente.nombre} ha sido creada',
            tipo='reserva'
        )

        return JsonResponse({
            'success': True,
            'reserva_id': reserva.id,
            'mensaje': 'Reserva creada exitosamente'
        })
        
    except Exception:
        return JsonResponse({'success': False, 'error': 'Error interno del servidor.'}, status=500)