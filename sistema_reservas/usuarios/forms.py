# usuarios/forms.py

from django import forms
from .models import Usuario

class BusquedaUsuarioForm(forms.Form):
    """Formulario para buscar y filtrar usuarios."""
    
    busqueda = forms.CharField(
        required=False, 
        label='Nombre, Apellidos o Documento',
        widget=forms.TextInput(attrs={'placeholder': 'Escribe nombre, apellido o documento', 'class': 'form-control'})
    )
    
    rol = forms.ChoiceField(
        required=False,
        label='Filtrar por Rol',
        choices=[('', 'Todos los Roles')] + list(Usuario.ROLES), 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    estado = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[
            ('', 'Todos'),
            ('activo', 'Activos'),
            ('inactivo', 'Inactivos')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class UsuarioEditForm(forms.ModelForm):
    """Formulario para editar datos de un usuario."""

    class Meta:
        model = Usuario
        fields = [
            'documento',
            'nombres',
            'apellidos',
            'email',
            'telefono',
            'rol',
            'activo',
        ]
        widgets = {
            'documento': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Configura el documento como solo lectura y telefono como obligatorio."""
        super().__init__(*args, **kwargs)
        if 'documento' in self.fields:
            self.fields['documento'].widget.attrs['readonly'] = 'readonly'
        self.fields['telefono'].required = True


class PerfilEditForm(forms.ModelForm):
    """Formulario para que un usuario edite su propio perfil."""

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'email', 'telefono']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telefono'].required = True