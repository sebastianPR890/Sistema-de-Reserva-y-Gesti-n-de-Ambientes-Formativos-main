from django import forms
from .models import Equipo, MovimientoEquipo

class EquipoForm(forms.ModelForm):
    """Formulario para crear y actualizar equipos."""
    
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
    
class MovimientoEquipoForm(forms.ModelForm):
    """Formulario para registrar movimientos de equipos."""
    
    class Meta:
        model = MovimientoEquipo
        fields = [
            'equipo', 'tipo_movimiento', 'ambiente_origen', 
            'ambiente_destino', 'usuario_responsable', 'observaciones',
            'autorizado_por'
        ]