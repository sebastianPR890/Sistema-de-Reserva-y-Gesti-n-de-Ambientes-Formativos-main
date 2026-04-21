import logging
from copy import deepcopy

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from notificaciones.models import Notificacion
from actividad.utils import registrar_actualizacion, capturar_cambios, registrar_actividad, capturar_todos_campos
from .forms import BusquedaUsuarioForm, UsuarioEditForm, PerfilEditForm
from .models import Usuario, SolicitudCambioRol

logger = logging.getLogger(__name__)

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
        # Capturar estado ANTES
        datos_antes = capturar_todos_campos(usuario)

        form = UsuarioEditForm(request.POST, instance=usuario)

        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = usuario.activo
            usuario.save()

            # Capturar estado DESPUÉS
            datos_despues = capturar_todos_campos(usuario)

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
                accion=f'Usuario actualizado: {usuario.nombre_completo()}',
                descripcion=descripcion_cambios if descripcion_cambios else 'Sin cambios detectados',
                modulo='usuarios',
                tipo_accion='UPDATE',
                objeto=usuario,
                datos_antes=datos_antes if cambios else None,
                datos_despues=datos_despues if cambios else None,
                request=request
            )

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
        # Capturar estado ANTES
        datos_antes = capturar_todos_campos(request.user)

        form = PerfilEditForm(request.POST, instance=request.user)
        if form.is_valid():
            usuario_actualizado = form.save()

            # Capturar estado DESPUÉS
            datos_despues = capturar_todos_campos(usuario_actualizado)

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
                accion=f'Perfil actualizado: {request.user.nombre_completo()}',
                descripcion=descripcion_cambios if descripcion_cambios else 'Sin cambios detectados',
                modulo='usuarios',
                tipo_accion='UPDATE',
                objeto=usuario_actualizado,
                datos_antes=datos_antes if cambios else None,
                datos_despues=datos_despues if cambios else None,
                request=request
            )

            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('usuarios:perfil')
        else:
            messages.error(request, 'Error al actualizar el perfil. Revisa los campos.')
    else:
        form = PerfilEditForm(instance=request.user)

    return render(request, 'usuarios/editar_perfil.html', {'form': form})

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

        registrar_actividad(
            usuario=request.user,
            accion=f'Solicitud de cambio de rol: {solicitud.get_rol_solicitado_display()}',
            descripcion=f'Rol actual: {solicitud.get_rol_actual_display()} → Solicitado: {solicitud.get_rol_solicitado_display()} | Razón: {razon}',
            modulo='usuarios',
            tipo_accion='CREATE',
            request=request,
        )
        messages.success(
            request,
            f'Solicitud de cambio de rol enviada correctamente. '
            f'Has solicitado el rol de "{solicitud.get_rol_solicitado_display()}". '
            f'Un administrador revisará tu solicitud pronto.'
        )

        # Crear notificación para administradores
        try:
            admins = Usuario.objects.filter(is_staff=True)
            for admin_user in admins:
                Notificacion.crear(
                    usuario=admin_user,
                    titulo='Nueva solicitud de cambio de rol',
                    mensaje=f'{usuario.nombre_completo()} ha solicitado cambiar su rol a {solicitud.get_rol_solicitado_display()}.',
                    tipo='sistema'
                )
        except Exception:
            logger.exception('Error al crear notificación de solicitud de cambio de rol')

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
        solicitud_antes = deepcopy(solicitud)
        solicitud.aprobar(request.user, comentario)

        # Registrar la actualización
        cambios = {
            'estado': {
                'antes': 'Pendiente',
                'después': 'Aprobada'
            },
            'rol': {
                'antes': solicitud_antes.usuario.rol,
                'después': solicitud.rol_solicitado
            }
        }
        registrar_actualizacion(
            usuario=request.user,
            objeto=f'Solicitud de rol - {solicitud.usuario.nombre_completo()}',
            cambios=cambios,
            modulo='usuarios',
            request=request
        )

        # Notificar al usuario
        try:
            Notificacion.crear(
                usuario=solicitud.usuario,
                titulo='Solicitud de rol aprobada',
                mensaje=f'Tu solicitud para el rol de {solicitud.get_rol_solicitado_display()} ha sido aprobada. '
                        f'{comentario if comentario else ""}',
                tipo='sistema'
            )
        except Exception:
            logger.exception('Error al crear notificación de aprobación de rol')

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

        # Registrar la actualización
        cambios = {
            'estado': {
                'antes': 'Pendiente',
                'después': 'Rechazada'
            }
        }
        registrar_actualizacion(
            usuario=request.user,
            objeto=f'Solicitud de rol - {solicitud.usuario.nombre_completo()}',
            cambios=cambios,
            modulo='usuarios',
            request=request
        )

        # Notificar al usuario
        try:
            Notificacion.crear(
                usuario=solicitud.usuario,
                titulo='Solicitud de rol rechazada',
                mensaje=f'Tu solicitud para el rol de {solicitud.get_rol_solicitado_display()} ha sido rechazada. '
                        f'{comentario if comentario else ""}',
                tipo='sistema'
            )
        except Exception:
            logger.exception('Error al crear notificación de rechazo de rol')

        messages.success(request, f'Solicitud de {solicitud.usuario.nombre_completo()} rechazada.')
        return redirect('usuarios:lista_solicitudes_rol')

    context = {'solicitud': solicitud}
    return render(request, 'usuarios/rechazar_solicitud_rol.html', context)
