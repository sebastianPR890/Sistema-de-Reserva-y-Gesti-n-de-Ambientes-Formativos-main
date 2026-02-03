from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Notificacion

@login_required
def listar_notificaciones(request):
    """Lista las notificaciones del usuario con filtros y paginación."""
    todas_notificaciones = request.user.notificaciones.all()
    estado_filtro = request.GET.get('estado', 'todas')
    
    if estado_filtro == 'no_leidas':
        todas_notificaciones = todas_notificaciones.filter(leida=False)
    elif estado_filtro == 'leidas':
        todas_notificaciones = todas_notificaciones.filter(leida=True)

    # Contadores para mostrar en la interfaz
    total_notificaciones = request.user.notificaciones.count()
    no_leidas = request.user.notificaciones.filter(leida=False).count()
    leidas = request.user.notificaciones.filter(leida=True).count()

    paginator = Paginator(todas_notificaciones, 10)
    page = request.GET.get('page')
    
    try:
        notificaciones = paginator.page(page)
    except (PageNotAnInteger, TypeError):
        notificaciones = paginator.page(1)
    except EmptyPage:
        notificaciones = paginator.page(paginator.num_pages)
    
    context = {
        'notificaciones': notificaciones,
        'estado_filtro': estado_filtro,
        'title': 'Mis Notificaciones',
        'total_notificaciones': total_notificaciones,
        'no_leidas': no_leidas,
        'leidas': leidas,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': notificaciones,
    }
    return render(request, 'notificaciones/listar_notificaciones.html', context)

@login_required
@require_POST
def marcar_como_leida(request, pk):
    """Marca una notificación específica como leída."""
    try:
        notificacion = request.user.notificaciones.get(pk=pk)
        if not notificacion.leida:
            notificacion.marcar_como_leida()
            return JsonResponse({
                'success': True, 
                'message': 'Notificación marcada como leída.'
            })
        return JsonResponse({
            'success': False, 
            'message': 'La notificación ya estaba marcada como leída.'
        })
    except Notificacion.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Notificación no encontrada o no pertenece al usuario.'
        }, status=404)

@login_required
@require_POST
def marcar_como_leidas_masiva(request):
    """Marca todas las notificaciones no leídas como leídas."""
    actualizadas = request.user.notificaciones.filter(leida=False).update(leida=True)
    messages.success(request, f'{actualizadas} notificaciones marcadas como leídas.')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'message': f'{actualizadas} notificaciones marcadas como leídas.',
            'actualizadas': actualizadas
        })
    return redirect('notificaciones:listar_notificaciones')

@login_required
def contar_no_leidas(request):
    """Retorna el número de notificaciones no leídas del usuario."""
    count = request.user.notificaciones.filter(leida=False).count()
    return JsonResponse({'no_leidas': count})