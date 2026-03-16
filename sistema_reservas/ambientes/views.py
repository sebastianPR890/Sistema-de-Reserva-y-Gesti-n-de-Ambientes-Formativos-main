from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from datetime import datetime
from copy import deepcopy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Ambiente
from .forms import AmbienteForm, BusquedaAmbienteForm, CrearAmbienteForm
from equipos.forms import EquipoForm, EquipoExternoForm
from equipos.models import Equipo
from actividad.utils import registrar_actualizacion, capturar_cambios, registrar_actividad

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que el usuario sea staff o coordinador."""
    def test_func(self):
        return self.request.user.puede_gestionar_recursos()

@login_required
def lista_ambientes(request):
    """Muestra la lista de ambientes con filtros de búsqueda."""
    form_busqueda = BusquedaAmbienteForm(request.GET)
    ambientes = Ambiente.objects.all()

    if form_busqueda.is_valid():
        cleaned_data = form_busqueda.cleaned_data
        
        busqueda = cleaned_data.get('busqueda')
        if busqueda:
            ambientes = ambientes.filter(
                Q(codigo__icontains=busqueda) | Q(nombre__icontains=busqueda)
            )
            
        tipo = cleaned_data.get('tipo')
        if tipo:
            ambientes = ambientes.filter(tipo=tipo)
            
        capacidad_min = cleaned_data.get('capacidad_min')
        if capacidad_min:
            ambientes = ambientes.filter(capacidad__gte=capacidad_min)

        solo_activos = cleaned_data.get('solo_activos')
        if solo_activos:
            ambientes = ambientes.filter(activo=True)
            
        con_computadores = cleaned_data.get('con_computadores')
        if con_computadores:
            ambientes = ambientes.filter(
                equipos__nombre__icontains='Computador' 
            ).distinct()
            
        con_escritorios = cleaned_data.get('con_escritorios')
        if con_escritorios:
            ambientes = ambientes.filter(
                equipos__nombre__icontains='Escritorio'
            ).distinct()
            
        con_tablero_digital = cleaned_data.get('con_tablero_digital')
        if con_tablero_digital:
            ambientes = ambientes.filter(
                equipos__nombre__icontains='Tablero Digital' 
            ).distinct()

    paginator = Paginator(ambientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form_busqueda': form_busqueda,
        'page_obj': page_obj,
        'ambientes': ambientes,
    }
    return render(request, 'ambientes/lista_ambientes.html', context)

class AmbienteUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Vista para editar un ambiente existente."""
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'ambientes/ambiente_form.html'
    success_url = reverse_lazy('ambientes:lista')

    def form_valid(self, form):
        # Capturar datos anteriores
        ambiente_antes = deepcopy(self.object)
        
        # Guardar el formulario
        response = super().form_valid(form)
        
        # Capturar cambios
        campos_a_comparar = ['nombre', 'codigo', 'descripcion', 'capacidad', 'tipo', 'ubicacion', 'activo']
        cambios = capturar_cambios(ambiente_antes, self.object, campos_a_comparar)
        
        # Registrar la actualización
        if cambios:
            registrar_actualizacion(
                usuario=self.request.user,
                objeto=f'Ambiente {self.object.nombre}',
                cambios=cambios,
                modulo='ambientes',
                request=self.request,
                instancia=self.object,
            )
        
        messages.success(self.request, "Ambiente actualizado exitosamente.")
        return response

class AmbienteDetailView(LoginRequiredMixin, DetailView):
    """Vista para mostrar los detalles de un ambiente."""
    model = Ambiente
    template_name = 'ambientes/ambiente_detalle.html'
    context_object_name = 'ambiente'

    def get_context_data(self, **kwargs):
        from reservas.models import Reserva
        from django.utils import timezone
        Reserva.cerrar_vencidas()
        context = super().get_context_data(**kwargs)
        # Para permisos del usuario logueado
        context['reserva_activa'] = Reserva.get_reserva_activa(self.object, self.request.user)
        # Responsable actual del aula: quien tenga reserva aprobada vigente (presente o futura)
        ahora = timezone.now()
        reserva_vigente = (
            Reserva.objects
            .filter(ambiente=self.object, estado='aprobada', fecha_fin__gte=ahora)
            .select_related('usuario')
            .order_by('fecha_inicio')
            .first()
        )
        context['responsable_actual'] = reserva_vigente.usuario if reserva_vigente else None
        context['reserva_vigente'] = reserva_vigente
        return context

class AmbienteDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """Vista para eliminar un ambiente."""
    model = Ambiente
    template_name = 'ambientes/ambiente_confirm_delete.html'
    success_url = reverse_lazy('ambientes:lista')

    def form_valid(self, form):
        messages.success(self.request, "Ambiente eliminado exitosamente.")
        return super().form_valid(form)
    
@login_required
def verificar_disponibilidad(request):
    """Vista AJAX para verificar la disponibilidad de un ambiente."""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        ambiente_id = request.GET.get('ambiente_id')
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        exclude_reserva_id = request.GET.get('exclude_reserva_id', None)

        if not all([ambiente_id, fecha_inicio_str, fecha_fin_str]):
            return JsonResponse({'disponible': False, 'mensaje': 'Faltan datos de la reserva.'}, status=400)

        try:
            ambiente = Ambiente.objects.get(pk=ambiente_id)
            fecha_inicio = datetime.fromisoformat(fecha_inicio_str)
            fecha_fin = datetime.fromisoformat(fecha_fin_str)
            
            disponible = ambiente.esta_disponible(fecha_inicio, fecha_fin, exclude_reserva_id)
            
            if disponible:
                mensaje = "El ambiente está disponible en las fechas seleccionadas."
            else:
                mensaje = "El ambiente no está disponible. Ya existe una reserva en ese período."
            
            return JsonResponse({'disponible': disponible, 'mensaje': mensaje})

        except Ambiente.DoesNotExist:
            return JsonResponse({'disponible': False, 'mensaje': 'El ambiente no existe.'}, status=404)
        except ValueError:
            return JsonResponse({'disponible': False, 'mensaje': 'Formato de fecha inválido.'}, status=400)

    return JsonResponse({'disponible': False, 'mensaje': 'Acceso no autorizado.'}, status=403)

@login_required
def crear_ambiente(request):
    """Permite crear un nuevo ambiente."""
    if not request.user.puede_gestionar_recursos():
        messages.error(request, 'No tienes permisos para crear ambientes')
        return redirect('ambientes:lista')
        
    if request.method == 'POST':
        form = CrearAmbienteForm(request.POST)
        if form.is_valid():
            ambiente = form.save()
            messages.success(request, f'Ambiente {ambiente.nombre} creado exitosamente')
            return redirect('ambientes:lista')
    else:
        form = CrearAmbienteForm()
    
    return render(request, 'ambientes/crear_ambiente.html', {'form': form})

@login_required
def agregar_equipo(request, ambiente_id):
    """
    Permite agregar un equipo (institucional o externo) a un ambiente.

    Tienen acceso:
    - Staff / coordinadores / admins (siempre).
    - El responsable activo del ambiente: usuario con reserva aprobada y vigente.
    """
    from reservas.models import Reserva

    ambiente = get_object_or_404(Ambiente, pk=ambiente_id)
    es_gestor = request.user.puede_gestionar_recursos()
    reserva_activa = Reserva.get_reserva_activa(ambiente, request.user)

    if not es_gestor and not reserva_activa:
        messages.error(request, 'No tienes permisos para agregar equipos a este ambiente.')
        return redirect('ambientes:detalle', pk=ambiente_id)

    # Tipo de equipo a registrar (GET param o POST)
    tipo = request.POST.get('tipo_equipo', request.GET.get('tipo_equipo', 'institucional'))
    es_externo = (tipo == 'externo')

    FormClass = EquipoExternoForm if es_externo else EquipoForm

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            equipo = form.save(commit=False)
            equipo.ambiente = ambiente
            equipo.responsable = request.user
            if es_externo:
                equipo.es_externo = True
                equipo.reserva_origen = reserva_activa
                # Código autogenerado para externos: EXT-<reserva_id>-<timestamp>
                from django.utils import timezone as tz
                equipo.codigo = f"EXT-{reserva_activa.pk if reserva_activa else 'manual'}-{tz.now().strftime('%Y%m%d%H%M%S')}"
            equipo.save()

            registrar_actividad(
                usuario=request.user,
                accion=f'Equipo {"externo" if es_externo else "institucional"} registrado: {equipo.nombre}',
                descripcion=f'Ambiente: {ambiente.nombre}' + (
                    f' | Propietario: {equipo.propietario_externo}' if es_externo else ''
                ),
                modulo='equipos',
                tipo_accion='CREATE',
                objeto=equipo,
                request=request,
            )
            messages.success(request, f'Equipo {equipo.nombre} agregado exitosamente.')
            return redirect('ambientes:detalle', pk=ambiente_id)
    else:
        form = FormClass()

    return render(request, 'equipos/equipo_form.html', {
        'form': form,
        'ambiente': ambiente,
        'es_externo': es_externo,
        'reserva_activa': reserva_activa,
    })