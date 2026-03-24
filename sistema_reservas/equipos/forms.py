from django import forms
from .models import Equipo, MovimientoEquipo


class EquipoForm(forms.ModelForm):
    """Formulario para crear y actualizar equipos institucionales."""

    class Meta:
        model = Equipo
        fields = [
            'codigo', 'nombre', 'descripcion', 'marca', 'modelo', 'serie',
            'ambiente', 'estado'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'ambiente': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['descripcion', 'marca', 'modelo', 'serie', 'ambiente']:
            self.fields[field_name].required = True


class EquipoResponsableForm(forms.ModelForm):
    """
    Formulario reducido para el responsable activo del ambiente.
    Solo permite cambiar el estado y la descripción del equipo.
    """

    class Meta:
        model = Equipo
        fields = ['estado', 'descripcion']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa el estado actual del equipo, daños observados, etc.'
            }),
        }
        labels = {
            'descripcion': 'Observaciones / Descripción del estado',
        }


class EquipoExternoForm(forms.ModelForm):
    """
    Formulario para registrar equipos externos (no pertenecen a la institución).
    Solo lo usan responsables activos de un ambiente durante su reserva.
    """

    class Meta:
        model = Equipo
        fields = [
            'nombre', 'descripcion', 'marca', 'modelo', 'serie',
            'propietario_externo', 'doc_propietario',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control',
                                             'placeholder': 'Ej: Laptop Dell Inspiron'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                 'placeholder': 'Características del equipo...'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': 'Número de serie (opcional)'}),
            'propietario_externo': forms.TextInput(attrs={'class': 'form-control',
                                                          'placeholder': 'Nombre completo del propietario'}),
            'doc_propietario': forms.TextInput(attrs={'class': 'form-control',
                                                      'placeholder': 'Documento del propietario'}),
        }
        labels = {
            'propietario_externo': 'Propietario',
            'doc_propietario': 'Documento del propietario',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['propietario_externo'].required = True
        self.fields['doc_propietario'].required = True
        self.fields['descripcion'].required = False
        self.fields['marca'].required = False
        self.fields['modelo'].required = False
        self.fields['serie'].required = False


class BusquedaEquipoForm(forms.Form):
    """Formulario para buscar y filtrar equipos."""

    busqueda = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por código, nombre o serie...',
            'class': 'form-control'
        })
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Equipo.ESTADOS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    activo = forms.BooleanField(required=False, initial=True, label='Solo activos')
    solo_externos = forms.BooleanField(required=False, label='Solo equipos externos')


class MovimientoEquipoForm(forms.ModelForm):
    """Formulario para solicitar un movimiento de equipo."""

    class Meta:
        model = MovimientoEquipo
        fields = [
            'equipo', 'tipo_movimiento', 'ambiente_origen',
            'ambiente_destino', 'observaciones',
        ]
        widgets = {
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                   'placeholder': 'Describe el motivo del movimiento...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ambiente_origen'].required = True
        self.fields['observaciones'].required = True


class RechazarMovimientoForm(forms.Form):
    """Formulario para rechazar un movimiento con motivo."""
    motivo_rechazo = forms.CharField(
        label='Motivo del rechazo',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explica por qué se rechaza el movimiento...',
        }),
        min_length=10,
    )