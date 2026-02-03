from django import forms
from .models import Notificacion
from usuarios.models import Usuario

class NotificacionForm(forms.ModelForm):
    class Meta:
        model = Notificacion
        fields = ['usuario', 'titulo', 'mensaje', 'tipo', 'leida']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'leida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }