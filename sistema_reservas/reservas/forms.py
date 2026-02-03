from django import forms
from .models import Reserva

class ReservaForm(forms.ModelForm):
    """Formulario para crear y editar reservas."""
    
    class Meta:
        model = Reserva
        fields = ['ambiente', 'fecha_inicio', 'fecha_fin', 'proposito', 'numero_asistentes']
        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
