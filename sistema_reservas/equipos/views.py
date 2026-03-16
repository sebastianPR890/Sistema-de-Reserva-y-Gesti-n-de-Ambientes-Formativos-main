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

from .models import Equipo, MovimientoEquipo
from .forms import EquipoForm, BusquedaEquipoForm, MovimientoEquipoForm, EquipoExternoForm, EquipoResponsableForm
from actividad.utils import registrar_actualizacion, capturar_cambios, registrar_actividad

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
        equipo_antes = deepcopy(self.object)
        response = super().form_valid(form)

        campos_a_comparar = ['codigo', 'nombre', 'serie', 'estado', 'descripcion', 'activo']
        cambios = capturar_cambios(equipo_antes, self.object, campos_a_comparar)

        if cambios:
            registrar_actualizacion(
                usuario=self.request.user,
                objeto=f'Equipo {self.object.nombre}',
                cambios=cambios,
                modulo='equipos',
                request=self.request,
                instancia=self.object,
            )

        # Alerta si el estado cambió a dañado o mantenimiento
        estado_nuevo = self.object.estado
        estado_viejo = equipo_antes.estado
        if estado_nuevo in ('dañado', 'mantenimiento') and estado_nuevo != estado_viejo:
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
        from reservas.models import Reserva
        from notificaciones.models import Notificacion
        from django.utils import timezone
        response = super().form_valid(form)

        # Verificar si alguno de los ambientes involucrados tiene reserva activa
        ahora = timezone.now()
        ambientes_a_verificar = [
            a for a in [self.object.ambiente_origen, self.object.ambiente_destino] if a
        ]
        sin_reserva = [
            a for a in ambientes_a_verificar
            if not Reserva.objects.filter(
                ambiente=a, estado='aprobada', fecha_fin__gte=ahora
            ).exists()
        ]
        if sin_reserva:
            nombres = ', '.join(a.nombre for a in sin_reserva)
            Notificacion.notificar_gestores(
                titulo='Movimiento de equipo sin reserva activa',
                mensaje=(
                    f'{self.request.user.nombre_completo()} registró un movimiento del equipo '
                    f'"{self.object.equipo.nombre}" ({self.object.equipo.codigo}). '
                    f'El siguiente ambiente no tiene reserva activa: {nombres}.'
                ),
                tipo='alerta',
            )

        messages.success(self.request, "Movimiento de equipo registrado exitosamente.")
        return response

class MovimientoEquipoListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    Vista para listar todos los movimientos de equipos.
    """
    model = MovimientoEquipo
    template_name = 'equipos/lista_movimientos.html'
    context_object_name = 'movimientos'
    paginate_by = 10
    ordering = ['-fecha_movimiento']