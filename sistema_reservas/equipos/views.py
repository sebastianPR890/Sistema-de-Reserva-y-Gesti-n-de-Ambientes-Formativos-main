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

from .models import Equipo, MovimientoEquipo
from .forms import EquipoForm, BusquedaEquipoForm, MovimientoEquipoForm

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
        
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

            if busqueda:
                queryset = queryset.filter(
                    Q(codigo__icontains=busqueda) |
                    Q(nombre__icontains=busqueda) |
                    Q(serie__icontains=busqueda)
                )
            if estado:
                queryset = queryset.filter(estado=estado)
            if activo:
                queryset = queryset.filter(activo=True)
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
        if not request.user.is_staff:
            messages.error(request, "No tienes permisos para crear equipos.")
            return redirect('ambientes:lista')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Equipo creado exitosamente.")
        return super().form_valid(form)

class EquipoUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    Vista genérica para editar un equipo existente.
    """
    model = Equipo
    form_class = EquipoForm
    template_name = 'equipos/equipo_form.html'
    success_url = reverse_lazy('equipos:lista')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "No tienes permisos para editar equipos.")
            return redirect('ambientes:lista')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ambiente'] = self.object.ambiente
        return context

    def form_valid(self, form):
        messages.success(self.request, "Equipo actualizado exitosamente.")
        return super().form_valid(form)

class EquipoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista genérica para mostrar los detalles de un equipo.
    """
    model = Equipo
    template_name = 'equipos/equipo_detalle.html'
    context_object_name = 'equipo'

class EquipoDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """
    Vista genérica para eliminar un equipo.
    """
    model = Equipo
    template_name = 'equipos/equipo_confirm_delete.html'
    success_url = reverse_lazy('equipos:lista')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
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
        # Redirige a la página de detalles del equipo después de un movimiento
        return reverse('equipos:equipo_detalle', kwargs={'pk': self.object.equipo.pk})
        
    def form_valid(self, form):
        messages.success(self.request, "Movimiento de equipo registrado exitosamente.")
        return super().form_valid(form)

class MovimientoEquipoListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    Vista para listar todos los movimientos de equipos.
    """
    model = MovimientoEquipo
    template_name = 'equipos/lista_movimientos.html'
    context_object_name = 'movimientos'
    paginate_by = 10
    ordering = ['-fecha_movimiento']