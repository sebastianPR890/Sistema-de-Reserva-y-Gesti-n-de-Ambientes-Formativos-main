from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import (
    CreateView, UpdateView, DetailView, DeleteView, ListView
)
from django.urls import reverse_lazy, reverse
from copy import deepcopy

from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST

from .models import Equipo, MovimientoEquipo
from .forms import EquipoForm, BusquedaEquipoForm, MovimientoEquipoForm, EquipoExternoForm, EquipoResponsableForm, RechazarMovimientoForm
from .utils import registrar_cambio_equipo
from actividad.utils import registrar_actualizacion, capturar_cambios, registrar_actividad, capturar_todos_campos

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.puede_gestionar_recursos()
        
    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para realizar esta acción.")
        return redirect('equipos:lista')

class EquipoListView(LoginRequiredMixin, ListView):
    model = Equipo
    template_name = 'equipos/equipo_list.html'
    context_object_name = 'equipos'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        form = BusquedaEquipoForm(self.request.GET)
        if form.is_valid():
            busqueda = form.cleaned_data.get('busqueda')
            estado = form.cleaned_data.get('estado')
            activo = form.cleaned_data.get('activo')
            solo_externos = form.cleaned_data.get('solo_externos')

            if busqueda:
                queryset = queryset.filter(
                    Q(codigo__icontains=busqueda) |
                    Q(nombre__icontains=busqueda) |
                    Q(serie__icontains=busqueda) |
                    Q(propietario_externo__icontains=busqueda)
                )
            if estado:
                queryset = queryset.filter(estado=estado)
            if activo:
                queryset = queryset.filter(activo=True)
            if solo_externos:
                queryset = queryset.filter(es_externo=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BusquedaEquipoForm(self.request.GET)
        return context

class EquipoCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    Vista genérica para crear un nuevo equipo.
    """
    model = Equipo
    form_class = EquipoForm
    template_name = 'equipos/equipo_form.html'
    success_url = reverse_lazy('equipos:lista')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.puede_gestionar_recursos():
            messages.error(request, "No tienes permisos para crear equipos.")
            return redirect('ambientes:lista')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        registrar_actividad(
            usuario=self.request.user,
            accion=f'Equipo creado: {self.object.nombre}',
            descripcion=f'Código: {self.object.codigo} | Ambiente: {self.object.ambiente}',
            modulo='equipos',
            tipo_accion='CREATE',
            objeto=self.object,
            request=self.request,
        )
        messages.success(self.request, "Equipo creado exitosamente.")
        return response

class EquipoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar un equipo.
    - Gestores (staff/coordinador): formulario completo.
    - Responsable activo del ambiente: solo puede cambiar estado y descripción.
    """
    model = Equipo
    template_name = 'equipos/equipo_form.html'
    success_url = reverse_lazy('equipos:lista')

    def _get_reserva_activa(self):
        from reservas.models import Reserva
        if self.object.ambiente:
            return Reserva.get_reserva_activa(self.object.ambiente, self.request.user)
        return None

    def dispatch(self, request, *args, **kwargs):
        # Necesitamos el objeto para verificar responsabilidad
        self.object = self.get_object()
        if not request.user.puede_gestionar_recursos():
            if not self._get_reserva_activa():
                messages.error(request, "No tienes permisos para editar este equipo.")
                ambiente_pk = self.object.ambiente.pk if self.object.ambiente else None
                return redirect('ambientes:detalle', pk=ambiente_pk) if ambiente_pk else redirect('ambientes:lista')
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        if self.request.user.puede_gestionar_recursos():
            return EquipoForm
        return EquipoResponsableForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ambiente'] = self.object.ambiente
        context['es_responsable'] = not self.request.user.puede_gestionar_recursos()
        return context

    def form_valid(self, form):
        from notificaciones.models import Notificacion

        # Guardar estado ANTES de cualquier cambio (directamente de la BD)
        equipo_db = Equipo.objects.get(pk=self.object.pk)
        datos_antes = capturar_todos_campos(equipo_db)

        # Guardar los cambios
        response = super().form_valid(form)

        # Capturar estado DESPUÉS de guardar
        datos_despues = capturar_todos_campos(self.object)

        # Comparar y detectar cambios
        cambios = {}
        for campo in datos_antes.keys():
            valor_antes = datos_antes.get(campo, '')
            valor_despues = datos_despues.get(campo, '')
            if str(valor_antes) != str(valor_despues):
                cambios[campo] = {
                    'antes': valor_antes,
                    'después': valor_despues
                }

        # Construir descripción de cambios
        descripcion_cambios = ""
        if cambios:
            cambios_formateados = []
            for campo, valores in cambios.items():
                antes = valores.get('antes', '—')
                despues = valores.get('después', '—')
                cambios_formateados.append(f"{campo}: {antes} → {despues}")
            descripcion_cambios = "\n".join(cambios_formateados)

        # Registrar actividad SIEMPRE
        registrar_actividad(
            usuario=self.request.user,
            accion=f'Equipo actualizado: {self.object.nombre}',
            descripcion=descripcion_cambios if descripcion_cambios else 'Sin cambios detectados',
            modulo='equipos',
            tipo_accion='UPDATE',
            objeto=self.object,
            datos_antes=datos_antes,
            datos_despues=datos_despues,
            request=self.request,
        )

        if cambios:
            # Registrar en el historial del equipo
            registrar_cambio_equipo(
                equipo_antes=equipo_db,
                equipo_despues=self.object,
                usuario=self.request.user,
                descripcion=descripcion_cambios
            )

            # Alerta si el estado cambió a dañado o mantenimiento
            if 'estado' in cambios:
                estado_nuevo = datos_despues.get('estado', '')
                if 'dañado' in estado_nuevo or 'mantenimiento' in estado_nuevo:
                    ambiente_nombre = self.object.ambiente.nombre if self.object.ambiente else 'Sin ambiente'
                    Notificacion.notificar_gestores(
                        titulo=f'Equipo {self.object.get_estado_display()}: {self.object.nombre}',
                        mensaje=(
                            f'{self.request.user.nombre_completo()} reportó el equipo '
                            f'"{self.object.nombre}" ({self.object.codigo}) '
                            f'en {ambiente_nombre} como {self.object.get_estado_display().lower()}.'
                        ),
                        tipo='alerta',
                    )

        messages.success(self.request, "Equipo actualizado exitosamente.")
        return response

class EquipoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista genérica para mostrar los detalles de un equipo.
    """
    model = Equipo
    template_name = 'equipos/equipo_detalle.html'
    context_object_name = 'equipo'

    def get_context_data(self, **kwargs):
        from reservas.models import Reserva
        from django.utils import timezone
        Reserva.cerrar_vencidas()
        context = super().get_context_data(**kwargs)
        es_responsable = False
        responsable_actual = None
        reserva_vigente = None
        if self.object.ambiente:
            es_responsable = Reserva.es_responsable_activo(self.object.ambiente, self.request.user)
            ahora = timezone.now()
            reserva_vigente = (
                Reserva.objects
                .filter(ambiente=self.object.ambiente, estado='aprobada', fecha_fin__gte=ahora)
                .select_related('usuario')
                .order_by('fecha_inicio')
                .first()
            )
            responsable_actual = reserva_vigente.usuario if reserva_vigente else None
        context['es_responsable'] = es_responsable
        context['responsable_actual'] = responsable_actual
        context['reserva_vigente'] = reserva_vigente
        return context

class EquipoDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """
    Vista genérica para eliminar un equipo.
    """
    model = Equipo
    template_name = 'equipos/equipo_confirm_delete.html'
    success_url = reverse_lazy('equipos:lista')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.puede_gestionar_recursos():
            messages.error(request, "No tienes permisos para eliminar equipos.")
            return redirect('ambientes:lista')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        registrar_actividad(
            usuario=self.request.user,
            accion=f'Equipo eliminado: {self.object.nombre}',
            descripcion=f'Código: {self.object.codigo} | Ambiente: {self.object.ambiente}',
            modulo='equipos',
            tipo_accion='DELETE',
            request=self.request,
        )
        messages.success(self.request, "Equipo eliminado exitosamente.")
        return super().form_valid(form)

class MovimientoEquipoCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    Vista para crear un nuevo movimiento de equipo.
    """
    model = MovimientoEquipo
    form_class = MovimientoEquipoForm
    template_name = 'equipos/movimiento_form.html'

    def get_success_url(self):
        return reverse('equipos:equipo_detalle', kwargs={'pk': self.object.equipo.pk})

    def form_valid(self, form):
        from notificaciones.models import Notificacion
        movimiento = form.save(commit=False)
        movimiento.usuario_responsable = self.request.user
        movimiento.estado = 'pendiente'
        movimiento.save()
        self.object = movimiento

        Notificacion.notificar_gestores(
            titulo='Solicitud de movimiento de equipo pendiente',
            mensaje=(
                f'{self.request.user.nombre_completo()} solicitó mover el equipo '
                f'"{movimiento.equipo.nombre}" ({movimiento.equipo.codigo}) '
                f'desde {movimiento.ambiente_origen or "externo"} '
                f'hacia {movimiento.ambiente_destino or "externo"}. '
                f'Requiere autorización.'
            ),
            tipo='alerta',
        )

        registrar_actividad(
            usuario=self.request.user,
            accion=f'Solicitud de movimiento: {movimiento.equipo.nombre}',
            descripcion=(
                f'Origen: {movimiento.ambiente_origen or "Externo"} → '
                f'Destino: {movimiento.ambiente_destino or "Externo"} | '
                f'Observaciones: {movimiento.observaciones}'
            ),
            modulo='equipos',
            tipo_accion='OTHER',
            objeto=movimiento.equipo,
            request=self.request,
        )
        messages.success(
            self.request,
            'Solicitud de movimiento registrada. Queda pendiente de autorización por un coordinador o administrador.'
        )
        return redirect(self.get_success_url())

@login_required
@require_POST
def autorizar_movimiento(request, pk):
    """Autoriza un movimiento pendiente. Solo coordinadores y admins."""
    if not request.user.puede_gestionar_recursos():
        return HttpResponseForbidden("No tienes permisos para autorizar movimientos.")

    movimiento = get_object_or_404(MovimientoEquipo, pk=pk)

    if movimiento.estado != 'pendiente':
        messages.warning(request, 'Este movimiento ya fue procesado.')
        return redirect('equipos:lista_movimientos')

    if movimiento.usuario_responsable == request.user:
        messages.error(request, 'No puedes autorizar tu propio movimiento.')
        return redirect('equipos:lista_movimientos')

    movimiento.estado = 'autorizado'
    movimiento.autorizado_por = request.user
    movimiento.save()

    # Actualizar ubicación del equipo
    equipo = movimiento.equipo
    if movimiento.tipo_movimiento == 'entrada' and movimiento.ambiente_destino:
        equipo.ambiente = movimiento.ambiente_destino
    elif movimiento.tipo_movimiento == 'salida':
        equipo.ambiente = None
    equipo.save()

    from notificaciones.models import Notificacion
    Notificacion.crear(
        usuario=movimiento.usuario_responsable,
        titulo='Movimiento autorizado',
        mensaje=(
            f'Tu solicitud de movimiento del equipo "{equipo.nombre}" '
            f'({movimiento.ambiente_origen or "externo"} → {movimiento.ambiente_destino or "externo"}) '
            f'fue autorizada por {request.user.nombre_completo()}.'
        ),
        tipo='equipo',
    )

    registrar_actividad(
        usuario=request.user,
        accion=f'Movimiento autorizado: {equipo.nombre}',
        descripcion=f'Movimiento #{movimiento.pk} autorizado.',
        modulo='equipos',
        tipo_accion='APPROVE',
        objeto=equipo,
        request=request,
    )

    messages.success(request, 'Movimiento autorizado. La ubicación del equipo ha sido actualizada.')
    return redirect('equipos:lista_movimientos')


@login_required
def rechazar_movimiento(request, pk):
    """Rechaza un movimiento pendiente con motivo obligatorio."""
    if not request.user.puede_gestionar_recursos():
        return HttpResponseForbidden("No tienes permisos para rechazar movimientos.")

    movimiento = get_object_or_404(MovimientoEquipo, pk=pk)

    if movimiento.estado != 'pendiente':
        messages.warning(request, 'Este movimiento ya fue procesado.')
        return redirect('equipos:lista_movimientos')

    if movimiento.usuario_responsable == request.user:
        messages.error(request, 'No puedes rechazar tu propio movimiento.')
        return redirect('equipos:lista_movimientos')

    if request.method == 'POST':
        form = RechazarMovimientoForm(request.POST)
        if form.is_valid():
            movimiento.estado = 'rechazado'
            movimiento.motivo_rechazo = form.cleaned_data['motivo_rechazo']
            movimiento.autorizado_por = request.user
            movimiento.save()

            from notificaciones.models import Notificacion
            Notificacion.crear(
                usuario=movimiento.usuario_responsable,
                titulo='Movimiento rechazado',
                mensaje=(
                    f'Tu solicitud de movimiento del equipo "{movimiento.equipo.nombre}" fue rechazada. '
                    f'Motivo: {movimiento.motivo_rechazo}'
                ),
                tipo='equipo',
            )

            registrar_actividad(
                usuario=request.user,
                accion=f'Movimiento rechazado: {movimiento.equipo.nombre}',
                descripcion=f'Movimiento #{movimiento.pk} rechazado. Motivo: {movimiento.motivo_rechazo}',
                modulo='equipos',
                tipo_accion='REJECT',
                objeto=movimiento.equipo,
                request=request,
            )

            messages.success(request, 'Movimiento rechazado. Se notificó al solicitante.')
            return redirect('equipos:lista_movimientos')
    else:
        form = RechazarMovimientoForm()

    return render(request, 'equipos/rechazar_movimiento.html', {
        'movimiento': movimiento,
        'form': form,
    })


class MovimientoEquipoListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    Vista para listar todos los movimientos de equipos.
    """
    model = MovimientoEquipo
    template_name = 'equipos/lista_movimientos.html'
    context_object_name = 'movimientos'
    paginate_by = 10
    ordering = ['-fecha_movimiento']