from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from .forms import BusquedaUsuarioForm, UsuarioEditForm
from .models import Usuario, SolicitudCambioRol
from django.db.models import Q

def es_admin(user):
    """Verifica si un usuario tiene permisos de administrador."""
    return user.is_staff

@login_required
@user_passes_test(es_admin)
def lista_usuarios(request):
    """Muestra lista de usuarios con opciones de búsqueda y filtrado."""
    usuarios = Usuario.objects.all().order_by('apellidos', 'nombres') 
    form_busqueda = BusquedaUsuarioForm(request.GET)
    
    if form_busqueda.is_valid():
        cleaned_data = form_busqueda.cleaned_data
        
        busqueda = cleaned_data.get('busqueda') 
        if busqueda:
            usuarios = usuarios.filter(
                Q(nombres__icontains=busqueda) | 
                Q(apellidos__icontains=busqueda) | 
                Q(documento__icontains=busqueda) 
            )
            
        rol = cleaned_data.get('rol') 
        if rol: 
            usuarios = usuarios.filter(rol=rol)

    paginator = Paginator(usuarios, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'usuarios': page_obj,
        'form_busqueda': form_busqueda,
        'page_obj': page_obj,
    }

    return render(request, 'usuarios/lista_usuarios.html', context)

@login_required
@user_passes_test(es_admin)
def detalle_usuario(request, pk):
    """Muestra los detalles de un usuario específico."""
    usuario = get_object_or_404(Usuario, pk=pk)
    return render(request, 'usuarios/detalle_usuario.html', {'usuario': usuario})

@login_required
@user_passes_test(es_admin)
def editar_usuario(request, pk):
    """Permite editar los datos de un usuario existente."""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = usuario.activo
            usuario.save()
            messages.success(request, f'Usuario {usuario.nombre_completo()} actualizado exitosamente.')
            return redirect('usuarios:lista_usuarios') 
        else:
            messages.error(request, '❌ Error al guardar los cambios. Revisa los campos.')
            
    else:
        form = UsuarioEditForm(instance=usuario)
        
    context = {
        'form': form,
        'usuario': usuario,
    }
    
    return render(request, 'usuarios/editar_usuario.html', context)

@login_required 
def perfil_usuario(request):
    """Muestra el perfil del usuario autenticado."""
    context = {
        'user': request.user,
    }
    return render(request, 'usuarios/perfil_usuario.html', context)

@login_required
def editar_perfil(request):
    """Permite al usuario editar su propio perfil."""
    if request.method == 'POST':
        user = request.user
        user.nombres = request.POST.get('nombres')
        user.apellidos = request.POST.get('apellidos')
        user.email = request.POST.get('email')
        user.telefono = request.POST.get('telefono')
        
        try:
            user.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('usuarios:perfil')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
    
    return render(request, 'usuarios/editar_perfil.html')

@login_required
def solicitar_cambio_rol(request):
    """Permite a usuarios normales solicitar cambio de rol."""
    # Verificar si ya tiene una solicitud pendiente
    solicitud_pendiente = SolicitudCambioRol.objects.filter(
        usuario=request.user,
        estado='pendiente'
    ).first()

    if request.method == 'POST':
        rol_solicitado = request.POST.get('rol_solicitado')
        razon = request.POST.get('razon', '')

        # Validar que el rol solicitado sea válido
        roles_permitidos = ['instructor', 'administrativo', 'coordinador']

        if rol_solicitado not in roles_permitidos:
            messages.error(request, 'Rol inválido.')
            return redirect('usuarios:solicitar_cambio_rol')

        # Verificar si ya tiene una solicitud pendiente
        if solicitud_pendiente:
            messages.warning(request, 'Ya tienes una solicitud de cambio de rol pendiente.')
            return redirect('usuarios:perfil')

        # Crear la solicitud en la base de datos
        usuario = request.user
        solicitud = SolicitudCambioRol.objects.create(
            usuario=usuario,
            rol_actual=usuario.rol,
            rol_solicitado=rol_solicitado,
            razon=razon
        )

        messages.success(
            request,
            f'Solicitud de cambio de rol enviada correctamente. '
            f'Has solicitado el rol de "{solicitud.get_rol_solicitado_display()}". '
            f'Un administrador revisará tu solicitud pronto.'
        )

        # Crear notificación para administradores
        try:
            from notificaciones.models import Notificacion
            admins = Usuario.objects.filter(is_staff=True)
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    titulo='Nueva solicitud de cambio de rol',
                    mensaje=f'{usuario.nombre_completo()} ha solicitado cambiar su rol a {solicitud.get_rol_solicitado_display()}.',
                    tipo='sistema'
                )
        except Exception:
            pass  # Si falla la notificación, no interrumpir el proceso

        return redirect('usuarios:perfil')

    context = {
        'roles_disponibles': [
            ('instructor', 'Instructor'),
            ('administrativo', 'Administrativo'),
            ('coordinador', 'Coordinador'),
        ],
        'solicitud_pendiente': solicitud_pendiente,
    }
    return render(request, 'usuarios/solicitar_cambio_rol.html', context)


@login_required
@user_passes_test(es_admin)
def lista_solicitudes_rol(request):
    """Muestra la lista de solicitudes de cambio de rol para administradores."""
    estado_filtro = request.GET.get('estado', 'pendiente')

    solicitudes = SolicitudCambioRol.objects.select_related('usuario', 'respondido_por')

    if estado_filtro and estado_filtro != 'todas':
        solicitudes = solicitudes.filter(estado=estado_filtro)

    # Contadores
    pendientes = SolicitudCambioRol.objects.filter(estado='pendiente').count()
    aprobadas = SolicitudCambioRol.objects.filter(estado='aprobada').count()
    rechazadas = SolicitudCambioRol.objects.filter(estado='rechazada').count()

    paginator = Paginator(solicitudes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'solicitudes': page_obj,
        'page_obj': page_obj,
        'estado_filtro': estado_filtro,
        'pendientes': pendientes,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
    }
    return render(request, 'usuarios/lista_solicitudes_rol.html', context)


@login_required
@user_passes_test(es_admin)
def aprobar_solicitud_rol(request, pk):
    """Aprueba una solicitud de cambio de rol."""
    solicitud = get_object_or_404(SolicitudCambioRol, pk=pk, estado='pendiente')

    if request.method == 'POST':
        comentario = request.POST.get('comentario', '')
        solicitud.aprobar(request.user, comentario)

        # Notificar al usuario
        try:
            from notificaciones.models import Notificacion
            Notificacion.objects.create(
                usuario=solicitud.usuario,
                titulo='Solicitud de rol aprobada',
                mensaje=f'Tu solicitud para el rol de {solicitud.get_rol_solicitado_display()} ha sido aprobada. '
                        f'{comentario if comentario else ""}',
                tipo='sistema'
            )
        except Exception:
            pass

        messages.success(
            request,
            f'Solicitud aprobada. {solicitud.usuario.nombre_completo()} ahora tiene el rol de {solicitud.get_rol_solicitado_display()}.'
        )
        return redirect('usuarios:lista_solicitudes_rol')

    context = {'solicitud': solicitud}
    return render(request, 'usuarios/aprobar_solicitud_rol.html', context)


@login_required
@user_passes_test(es_admin)
def rechazar_solicitud_rol(request, pk):
    """Rechaza una solicitud de cambio de rol."""
    solicitud = get_object_or_404(SolicitudCambioRol, pk=pk, estado='pendiente')

    if request.method == 'POST':
        comentario = request.POST.get('comentario', '')
        solicitud.rechazar(request.user, comentario)

        # Notificar al usuario
        try:
            from notificaciones.models import Notificacion
            Notificacion.objects.create(
                usuario=solicitud.usuario,
                titulo='Solicitud de rol rechazada',
                mensaje=f'Tu solicitud para el rol de {solicitud.get_rol_solicitado_display()} ha sido rechazada. '
                        f'{comentario if comentario else ""}',
                tipo='sistema'
            )
        except Exception:
            pass

        messages.success(request, f'Solicitud de {solicitud.usuario.nombre_completo()} rechazada.')
        return redirect('usuarios:lista_solicitudes_rol')

    context = {'solicitud': solicitud}
    return render(request, 'usuarios/rechazar_solicitud_rol.html', context)
