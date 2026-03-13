from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import render

from .models import RegistroActividad


def es_admin_o_coordinador(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or user.rol == 'coordinador'
    )


@login_required
@user_passes_test(es_admin_o_coordinador)
def lista_actividad(request):
    actividades = RegistroActividad.objects.select_related('usuario').exclude(modulo='sesion')

    filtro_modulo = request.GET.get('modulo', '')
    filtro_busqueda = request.GET.get('busqueda', '')
    filtro_fecha_desde = request.GET.get('fecha_desde', '')
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '')

    if filtro_modulo:
        actividades = actividades.filter(modulo=filtro_modulo)
    if filtro_busqueda:
        actividades = actividades.filter(accion__icontains=filtro_busqueda) | \
                      actividades.filter(descripcion__icontains=filtro_busqueda) | \
                      actividades.filter(usuario__nombres__icontains=filtro_busqueda) | \
                      actividades.filter(usuario__apellidos__icontains=filtro_busqueda)
    if filtro_fecha_desde:
        actividades = actividades.filter(fecha__date__gte=filtro_fecha_desde)
    if filtro_fecha_hasta:
        actividades = actividades.filter(fecha__date__lte=filtro_fecha_hasta)

    total = actividades.count()

    paginator = Paginator(actividades, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Contadores por módulo (excluyendo sesión)
    contadores = {modulo: RegistroActividad.objects.filter(modulo=modulo).exclude(modulo='sesion').count()
                  for modulo, _ in RegistroActividad.MODULOS if modulo != 'sesion'}

    context = {
        'page_obj': page_obj,
        'actividades': page_obj,
        'modulos': RegistroActividad.MODULOS,
        'filtro_modulo': filtro_modulo,
        'filtro_busqueda': filtro_busqueda,
        'filtro_fecha_desde': filtro_fecha_desde,
        'filtro_fecha_hasta': filtro_fecha_hasta,
        'total': total,
        'contadores': contadores,
    }
    return render(request, 'actividad/lista_actividad.html', context)
